"""PyVista helpers: surface heat maps of FEA results (von Mises), deformed shapes, consistent styling."""
import numpy as np, pyvista as pv
pv.OFF_SCREEN = True
def grid(mesh, vm=None, u=None, scale=1.0):
    cells = np.hstack([np.full((mesh.nelements, 1), 4), mesh.t.T]).ravel()
    g = pv.UnstructuredGrid(cells, np.full(mesh.nelements, pv.CellType.TETRA), (mesh.p.T + (scale * u.T if u is not None else 0)).astype(float))
    if vm is not None: g.point_data["von Mises (MPa)"] = vm
    return g
def heatmap(g, path, title, cam=None, clim=None, size=(1600, 1000), ghost=None, annotate=None, fmt="%.0f"):
    p = pv.Plotter(off_screen=True, window_size=size); p.set_background("#F4F1EA", top="#FFFFFF")
    if ghost is not None: p.add_mesh(ghost, color="#9AA3AE", opacity=0.18, style="wireframe", line_width=.5)
    p.add_mesh(g.extract_surface(algorithm="dataset_surface"), scalars="von Mises (MPa)", cmap="turbo", clim=clim, smooth_shading=True, show_edges=False,
               scalar_bar_args=dict(title="von Mises stress (MPa)", vertical=True, position_x=.86, position_y=.15, height=.7, width=.05, title_font_size=18, label_font_size=16, color="#14213D", fmt=fmt))
    p.add_text(title, position="upper_left", font_size=13, color="#14213D")
    if annotate:
        for pt, txt in annotate: p.add_point_labels([pt], [txt], font_size=16, point_color="#14213D", point_size=10, text_color="#14213D", shape_color="white", shape_opacity=.85, always_visible=True)
    if cam: p.camera_position = cam
    else: p.view_isometric(); p.camera.zoom(1.2)
    p.enable_anti_aliasing("ssaa"); p.screenshot(path); p.close()
