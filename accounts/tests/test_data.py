import json

from django.conf import settings

# M-Pesa Reference Number
mpesa_reference_no = "NLJ7RT61SV"

CheckoutRequestID = "ws_CO_191220191020363925"
MerchantRequestID = "29115-34620561-1"
# M-Pesa STKPush response
mock_stk_push_response = {
    "MerchantRequestID": MerchantRequestID,
    "CheckoutRequestID": CheckoutRequestID,
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CustomerMessage": "Success. Request accepted for processing",
}

# M-Pesa STKPush result
mock_stk_push_result = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": MerchantRequestID,
            "CheckoutRequestID": CheckoutRequestID,
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {"Name": "Amount", "Value": 1.00},
                    {"Name": "MpesaReceiptNumber", "Value": mpesa_reference_no},
                    {"Name": "TransactionDate", "Value": 20191219102115},
                    {"Name": "PhoneNumber", "Value": 254712345678},
                ]
            },
        }
    }
}


# Sample of failed STKPush response
mock_failed_stk_push_response = {
    "Body": {
        "stkCallback": {
            "MerchantRequestID": MerchantRequestID,
            "CheckoutRequestID": CheckoutRequestID,
            "ResultCode": 1032,
            "ResultDesc": "Request canceled by user.",
        }
    }
}

# Transaction instance to be saved in Transaction model
sample_positive_transaction_instance_info = {
    "account": "+254704845040",
    "external_transaction_id": mpesa_reference_no,
    "cash_flow": "INWARD",
    "type": "DEPOSIT",
    "status": "SUCCESSFUL",
    "service": "MPESA",
    "description": "",
    "amount": 1.0,
    "external_response": json.dumps({}),
}

sample_transaction_instance_deposit_1000 = {
    "account": "+254704845040",
    "external_transaction_id": mpesa_reference_no,
    "cash_flow": "INWARD",
    "type": "DEPOSIT",
    "status": "SUCCESSFUL",
    "service": "MPESA",
    "description": "",
    "amount": 1000.0,
    "external_response": json.dumps({}),
}


sample_negative_transaction_instance_info = {
    "account": "+254704845040",
    "external_transaction_id": "RANDOMTRANSID45",
    "cash_flow": "OUTWARD",
    "type": "WITHDRAWAL",
    "status": "SUCCESSFUL",
    "service": "MPESA",
    "description": "",
    "amount": 20.0,
    "fee": 1.0,
    "external_response": json.dumps({}),
}

# M-Pesa Paybill Response

mock_paybill_deposit_response = {
    "TransactionType": "Pay Bill",
    "TransID": "RKTQDM7W6S",
    "TransTime": "20191122063845",
    "TransAmount": "10",
    "BusinessShortCode": settings.MPESA_BUSINESS_SHORT_CODE,
    "BillRefNumber": "+254704845040",
    "InvoiceNumber": "",
    "OrgAccountBalance": "35.00",
    "ThirdPartyTransID": "",
    "MSISDN": "+254704845040",
    "FirstName": "WARUI",
    "MiddleName": "NGUGI",
    "LastName": "NGUGI",
}


# M-Pesa B2C sample data
CONVERSATION_ID = "AG_20191219_00005797af5d7d75f652"
sample_b2c_response = {
    "ConversationID": CONVERSATION_ID,
    "OriginatorConversationID": "16740-34861180-1",
    "ResponseCode": "0",
    "ResponseDescription": "Accept the service request successfully.",
}
sample_failed_b2c_response = {
    "requestId": "11728-2929992-1",
    "errorCode": "401.002.01",
    "errorMessage": "Error Occurred - Invalid Access Token - BJGFGOXv5aZnw90KkA4TDtu4Xdyf",
}


withdrawal_obj_instance = {
    "conversation_id": CONVERSATION_ID,
    "originator_conversation_id": "16740-34861180-1",
    "response_code": "0",
    "response_description": "Accept the service request successfully.",
    "transaction_amount": 10,
    "phone_number": "+254704845040",
}

mock_failed_b2c_result = {
    "Result": {
        "ResultType": 0,
        "ResultCode": 2001,
        "ResultDesc": "The initiator information is invalid.",
        "OriginatorConversationID": "29112-34801843-1",
        "ConversationID": CONVERSATION_ID,
        "TransactionID": "NLJ0000000",
        "ReferenceData": {
            "ReferenceItem": {
                "Key": "QueueTimeoutURL",
                "Value": "https:\/\/internalsandbox.safaricom.co.ke\/mpesa\/b2cresults\/v1\/submit",
            }
        },
    }
}

mock_successful_b2c_result = {
    "Result": {
        "ResultType": 0,
        "ResultCode": 0,
        "ResultDesc": "The service request is processed successfully.",
        "OriginatorConversationID": "29112-34801843-1",
        "ConversationID": CONVERSATION_ID,
        "TransactionID": "REH3SOIU9T",
        "ResultParameters": {
            "ResultParameter": [
                {"Key": "TransactionAmount", "Value": 10},
                {"Key": "TransactionReceipt", "Value": "REH3SOIU9T"},
                {"Key": "B2CRecipientIsRegisteredCustomer", "Value": "Y"},
                {"Key": "B2CChargesPaidAccountAvailableFunds", "Value": -451.00},
                {"Key": "ReceiverPartyPublicName", "Value": "254708374149 - John Doe"},
                {"Key": "TransactionCompletedDateTime", "Value": "19.12.2019 11:45:50"},
                {"Key": "B2CUtilityAccountAvailableFunds", "Value": 101.00},
                {"Key": "B2CWorkingAccountAvailableFunds", "Value": 900.00},
            ]
        },
        "ReferenceData": {
            "ReferenceItem": {
                "Key": "QueueTimeoutURL",
                "Value": "https:\/\/internalsandbox.safaricom.co.ke\/mpesa\/b2cresults\/v1\/submit",
            }
        },
    }
}
