class Config:
    model = "flux-dev" #目前支持传入 "flux-schnell" 和 "flux-dev"，理论上支持百炼其他DashScope SDK调用文生图模型，已测试wanx2.1-t2i-plus可用。
    size = "768*1024" #支持"512*1024, 768*512, 768*1024, 1024*576, 576*1024, 1024*1024"六种分辨率。
    DASHSCOPE_API_KEY = "YOUR_DASHSCOPE_API_KEY" #阿里云百炼平台的API Key。
