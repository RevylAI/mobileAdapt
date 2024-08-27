from fastapi import APIRouter, Depends
from pydantic import BaseModel
# Import other necessary modules and functions

router = APIRouter()

@router.get("/health_check")
async def health_check():
    '''
    Health check endpoint to verify server is running
    '''
    return {"status": "running", "message": "Server is up and running"}

@router.post('/locate_element')
async def locate_element(step_info: StepInfo, user_id: AuthInfo = Depends(get_current_user_uuid)):
    '''
    Locate element on the device and highlight the element
    input: step_info
    '''
    start_device_info = StartDeviceInfo(
        platform=step_info.platform,
        app_package=step_info.app_package,
        email=step_info.email,
        user_id=step_info.user_id,
        local=step_info.local,
        test_id=step_info.test_id
    )
    cognisim: CogniSim = await setup_device(start_device_info, auth_info=user_id)
    step_type = step_info.task['step_type']
    step_description = step_info.task['step']
    # Step metadata to check for selectors etc
    step_metadata = step_info.task.get('metadata', {})
    # Get the element and then also highlight it
    element_id = await cognisim.locate_element(step_metadata, step_type, step_description)
    return {'result': element_id}

@router.post('/execute_step')
async def execute_step(step_info: StepInfo, user_id: AuthInfo = Depends(get_current_user_uuid)):
    '''
    Execute a step on device
    also need a call to backend api for decrementing test
    Route based on platform
    '''

    # Placeholder for actual implementation
    start_device_info = StartDeviceInfo(
        platform=step_info.platform,
        app_package=step_info.app_package,
        email=step_info.email,
        user_id=step_info.user_id,
        local=step_info.local,
        test_id=step_info.test_id
    )
    # TODO add speed choices
    start_time = time.time()
    # .37 seconds on api call here ~370ms
    cognisim: CogniSim = await setup_device(start_device_info, auth_info=user_id)
    end_time = time.time()
    setup_duration = end_time - start_time
    logger.info(f"Device setup took {setup_duration:.2f} seconds")
    step_type = step_info.task['step_type']
    step_metadata = step_info.task.get('metadata', {})
    execution_api_client = get_execution_api_client(user_id.api_key)
    step_description = step_info.task['step']
    step_multimodal = step_info.task.get('multimodal', step_info.multimodal)
    step_download = step_info.task.get('download', step_info.download)
    logger.info(f"Step download: {step_download}")
    # Execute Step on device
    action_grounded = await cognisim.run_step(step_type, step_description, multimodal=step_multimodal, step_metadata=step_metadata, download=step_download, speed=Speed.FAST)
    run_info = json.dumps(action_grounded, cls=CustomJSONEncoder)
    # Decrement executions on the account
    execution_api_client.decrement_test_executions(
        uid=user_id.user_id, decrement_by=1)