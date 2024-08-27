from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from device.device_factory import DeviceFactory
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class MobileAdapter:
    def __init__(self):
        self.device = None

    async def initialize_device(self, platform: str, app_url: str):
        self.device = DeviceFactory.create_device(platform, app_url)
        await self.device.start_device()

    async def get_state(self):
        if self.device is None:
            return {"error": "Device not initialized"}
        return await self.device.get_state()

    async def perform_action(self, action_type: str, **kwargs): 
        if self.device is None:
            return {"error": "Device not initialized"}
        if action_type == "tap":
            await self.device.tap(kwargs.get("x"), kwargs.get("y"))
        elif action_type == "input":
            await self.device.input(kwargs.get("x"), kwargs.get("y"), kwargs.get("text"))
        elif action_type == "swipe":
            await self.device.swipe(kwargs.get("x"), kwargs.get("y"), kwargs.get("direction"))
        else:
            return {"error": "Invalid action type"}
        return {"status": "Action performed"}

mobile_adapter = MobileAdapter()

class InitializeRequest(BaseModel):
    platform: str
    app_url: str

@app.post("/initialize")
async def initialize(request: InitializeRequest):
    await mobile_adapter.initialize_device(request.platform, request.app_url)
    return {"status": "Device initialized"}

@app.get("/state")
async def get_state():
    return await mobile_adapter.get_state()

@app.post("/action")
async def perform_action(action_type: str, **kwargs):
    return await mobile_adapter.perform_action(action_type, **kwargs)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)