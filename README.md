# SimpleDiscord

### Setup
Dependencies:
```Bash
conda env create -f environment.yaml -n simple-discord
conda activate simple-discord
```
Dynamodb Local Setup (make sure you have docker desktop installed and its running):
```Bash
docker run -p 8000:8000 amazon/dynamodb-local
```
Run the application (on port 8080):
```Bash
uvicorn main:app --reload --port 8080
```
Do a post request:
POST http://localhost:8080/messages
body:
```json
{
  "chat_id": "1",
  "timestamp": 0,
  "user_id": "0",
  "content": "hello"
}
```
Do a get request:
GET http://localhost:8080/messages/1