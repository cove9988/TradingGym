0. Check if you have Nvidia graphics card. Go to 'Device Manager' in windows, and expand 'Display Adapters'. It will show here if you have. 

1. Install CUDA Download the NVIDIA CUDA Toolkit
https://developer.nvidia.com/cuda-dow...

2. Install PyTorch: 
https://pytorch.org/get-started/locally/

3. Check version of CUDA by running this command in git bash: 
nvcc -V

4. Paste installation command into git bash. 

5. Check installation: 
import torch
print(torch.rand(5, 3))
torch.cuda.is_available()
