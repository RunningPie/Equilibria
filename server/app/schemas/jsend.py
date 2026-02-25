from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from enum import Enum
from fastapi.responses import JSONResponse
from fastapi import status

'''
Generic digunakan untuk memberitahu class dia akan menerima tipe data generik
Optional digunakan untuk menandakan bahwa field tersebut bisa bernilai None
TypeVar digunakan untuk membuat tipe data generik yang bisa digunakan di seluruh class

BaseModel digunakan untuk membuat model data yang bisa divalidasi oleh Pydantic
Field digunakan untuk memberikan metadata pada field, seperti contoh value, deskripsi, dll

Enum digunakan untuk membuat enumerasi, yaitu tipe data yang memiliki nilai terbatas
'''

class JSendStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"

T = TypeVar('T')

class JSendResponse(BaseModel, Generic[T]):
    status: JSendStatus = Field(..., description="Status of the response: 'success', 'fail', or 'error'")
    code: int = Field(..., description="HTTP status code, can be 2XX for success, 4XX for client errors, and 5XX for server errors")
    message: str = Field(..., description="Error or informational message, required for every response")
    data: Optional[T] = Field(None, description="Data payload for 'success' responses, none in case of 'error' and 'fail' responses")
    
    def to_JSON(self) -> dict:
        '''
        Convert JSendResponse to JSONResponse object
        agar kode statusnya sesuai status
        '''
        return JSONResponse(
            status_code=self.code,
            content=self.model_dump(mode='json')
        )
    
class Config:
    json_scheme_extra = {
        "example":{
            "status": "success",
            "code": 200,
            "message": "Request processed successfully",
            "data": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "full_name": "John Doe",
                "nim": "1234567890"
            }
        }
    }
    
# === HElper ====

def jsend_success(code: int, data: T, message: str = "Request processed successfully") -> JSONResponse:
    '''
    Helper untuk membuat response JSend dengan status 'success'
    '''
    return JSendResponse(
        status=JSendStatus.SUCCESS,
        code=code,
        message=message,
        data=data
    ).to_JSON()

def jsend_fail(code: int, message: str = "Request failed due to client error") -> JSONResponse:
    '''
    Helper untuk membuat response JSend dengan status 'fail'
    '''
    return JSendResponse(
        status=JSendStatus.FAIL,
        code=code,
        message=message,
        data=None
    ).to_JSON()

def jsend_error(code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, message: str = "An error occurred on the server") -> JSONResponse:
    '''
    Helper untuk membuat response JSend dengan status 'error'
    '''
    return JSendResponse(
        status=JSendStatus.ERROR,
        code=code,
        message=message,
        data=None
    ).to_JSON()