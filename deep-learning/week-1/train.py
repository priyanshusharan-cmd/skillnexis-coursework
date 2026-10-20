"""Synthetic numerical pattern regression; run with PyTorch and Matplotlib installed."""
import torch
from torch import nn
import matplotlib.pyplot as plt
torch.manual_seed(7)
x=torch.linspace(-2,2,500).reshape(-1,1); y=3*x+0.7+0.15*torch.randn_like(x)
train_x,val_x=x[:400],x[400:];train_y,val_y=y[:400],y[400:]
class Net(nn.Module):
 def __init__(self): super().__init__(); self.layers=nn.Sequential(nn.Linear(1,16),nn.ReLU(),nn.Linear(16,1))
 def forward(self,x): return self.layers(x)
results={}
for lr in (0.01,0.05):
 model=Net();opt=torch.optim.SGD(model.parameters(),lr=lr);loss_fn=nn.MSELoss(); train_hist=[];val_hist=[]
 for epoch in range(200):
  model.train();opt.zero_grad();loss=loss_fn(model(train_x),train_y);loss.backward();opt.step()
  model.eval()
  with torch.no_grad(): train_hist.append(loss_fn(model(train_x),train_y).item());val_hist.append(loss_fn(model(val_x),val_y).item())
 results[lr]=(model,train_hist,val_hist)
 print(f'lr={lr}: final train={train_hist[-1]:.4f}; validation={val_hist[-1]:.4f}')
plt.figure();
for lr,(_,tr,va) in results.items(): plt.plot(va,label=f'validation lr={lr}')
plt.xlabel('Epoch');plt.ylabel('MSE');plt.legend();plt.tight_layout();plt.savefig('loss_curve.png',dpi=150)
model=results[0.01][0];model.eval()
with torch.no_grad(): pred=model(val_x)
plt.figure();plt.scatter(val_x.numpy(),val_y.numpy(),s=10,label='actual');plt.scatter(val_x.numpy(),pred.numpy(),s=10,label='predicted');plt.legend();plt.tight_layout();plt.savefig('actual_vs_predicted.png',dpi=150)
