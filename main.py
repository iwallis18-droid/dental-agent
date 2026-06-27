from fastapi import FastAPI, HTTPException, Header
import pydantic
import httpx
import os

app = FastAPI()

# This is the endpoint Retell will talk to when a call ends
@app.post("/webhook/booking")
async def handle_dental_booking(
    payload: dict, 
    x_retell_secret: str = Header(None, alias="X-Retell-Secret")
):
   # 1. Security Check: Make sure the call is actually coming from your Retell account
    if x_retell_secret != os.environ.get("RETELL_SECRET_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    # 2. Extract the data points Retell collected during the phone call
    # (We use .get() to prevent crashing if the data is missing)
    args = payload.get("call_analysis", {}).get("custom_analysis_data", 
{})
    
    first_name = args.get("patient_first_name")
    last_name = args.get("patient_last_name")
    dob = args.get("patient_dob")
    requested_slot = args.get("requested_slot")
    clinic_id = args.get("clinic_id") 

    # 3. Format the data to match exactly what your Dental API middleware 
expects
    pms_mapped_payload = {
        "practiceId": clinic_id,
        "patient": {
            "firstName": first_name,
            "lastName": last_name,
            "dob": dob
        },
        "appointment": {
            "startTime": requested_slot,
            "type": "Hygiene_Cleaning"
        }
    }
    
    # 4. Push the data directly to your Unified Dental API middleware
    middleware_url =
 "https://hook.us2.make.com/2ir8dddrancgexcghhtmowgfl44kt32xs"
    headers = {
        "Authorization": f"Bearer {os.environ.get('UNIFIED_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(middleware_url, 
json=pms_mapped_payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="PMS write-back 
failed")
            
    return {"status": "success", "message": "Appointment pushed to PMS"}

