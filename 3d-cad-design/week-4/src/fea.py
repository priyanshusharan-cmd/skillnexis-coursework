"""Small linear-elastic solid FEA toolkit: CadQuery geometry -> gmsh tetrahedral mesh -> scikit-fem quadratic (P2)
tetrahedra -> displacement, von Mises stress. Units: mm, N, MPa.
Quadratic elements are used because linear tets are far too stiff in bending ("locking")."""
import numpy as np, gmsh, cadquery as cq
import skfem as fem
from skfem.models.elasticity import linear_elasticity, lame_parameters
from skfem.helpers import dot, sym_grad
import scipy.sparse.linalg as spla
import pyamg
def mesh_from_cq(shape, h, path="build/_g.step"):
    """Tetrahedral mesh of a CadQuery solid with target element size h (mm)."""
    cq.exporters.export(cq.Workplane().add(shape), path)
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0); gmsh.model.add("m"); gmsh.model.occ.importShapes(path); gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h); gmsh.option.setNumber("Mesh.MeshSizeMin", h / 4); gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1); gmsh.model.mesh.generate(3); gmsh.model.mesh.optimize("Netgen")
    tags, xyz, _ = gmsh.model.mesh.getNodes(); xyz = xyz.reshape(-1, 3)
    et, etags, enodes = gmsh.model.mesh.getElements(3); tets = enodes[0].reshape(-1, 4)
    idx = {t: i for i, t in enumerate(tags)}; t = np.vectorize(idx.get)(tets)
    used = np.unique(t); remap = -np.ones(len(xyz), int); remap[used] = np.arange(len(used))
    gmsh.finalize()
    return fem.MeshTet(xyz[used].T.copy(), remap[t].T.copy())
class Model:
    def __init__(self, mesh, E, nu, order=2):
        self.m = mesh; self.E, self.nu = E, nu
        el = fem.ElementVector(fem.ElementTetP2() if order == 2 else fem.ElementTetP1())
        self.ib = fem.Basis(mesh, el, intorder=2 * order); self.K = fem.asm(linear_elasticity(*lame_parameters(E, nu)), self.ib)
        self.f = np.zeros(self.K.shape[0]); self.fixed = np.array([], int)
    def fix(self, where):
        """Fix all displacement components on boundary facets where(x) is True (x is 3 x n midpoints)."""
        facets = self.m.facets_satisfying(where, boundaries_only=True); dofs = self.ib.get_dofs(facets).all()
        self.fixed = np.union1d(self.fixed, dofs); return len(facets)
    def traction(self, where, total_force):
        """Uniform traction on facets where(x), scaled so its resultant equals total_force (3-vector, N)."""
        facets = self.m.facets_satisfying(where, boundaries_only=True); fb = fem.FacetBasis(self.m, self.ib.elem, facets=facets, intorder=4)
        area = fem.asm(fem.Functional(lambda w: 1.0 + 0 * w.x[0]), fb); tvec = np.array(total_force) / area
        @fem.LinearForm
        def load(v, w): return v[0] * tvec[0] + v[1] * tvec[1] + v[2] * tvec[2]
        self.f += fem.asm(load, fb); return area
    def solve(self):
        I = self.ib.complement_dofs(self.fixed); A = self.K[I][:, I].tocsr(); b = self.f[I]
        ml = pyamg.smoothed_aggregation_solver(A, B=None, max_coarse=500); x, info = spla.cg(A, b, M=ml.aspreconditioner(), rtol=1e-10, maxiter=2000)
        assert info == 0, "solver did not converge"
        self.u = np.zeros(self.K.shape[0]); self.u[I] = x; return self.u
    def von_mises(self):
        """Nodal von Mises stress (MPa): stresses at quadrature points, L2-projected to a continuous P1 field."""
        lam, mu = lame_parameters(self.E, self.nu); uh = self.ib.interpolate(self.u); eps = sym_grad(uh)
        tr = eps[0, 0] + eps[1, 1] + eps[2, 2]; s = [[2 * mu * eps[i, j] + (lam * tr if i == j else 0) for j in range(3)] for i in range(3)]
        vm = np.sqrt(.5 * ((s[0][0] - s[1][1]) ** 2 + (s[1][1] - s[2][2]) ** 2 + (s[2][2] - s[0][0]) ** 2) + 3 * (s[0][1] ** 2 + s[1][2] ** 2 + s[0][2] ** 2))
        pb = fem.Basis(self.m, fem.ElementTetP1(), quadrature=self.ib.quadrature)
        M = fem.asm(fem.BilinearForm(lambda u, v, w: u * v), pb); rhs = fem.asm(fem.LinearForm(lambda v, w: w["vm"] * v), pb, vm=vm)
        self.vm = spla.spsolve(M.tocsc(), rhs); return self.vm
    def nodal_disp(self):
        """Displacement at the mesh vertices (3 x nverts)."""
        return self.u[self.ib.nodal_dofs[:, :self.m.nvertices]] if self.u.ndim else None
    def ndofs(self): return self.K.shape[0]
