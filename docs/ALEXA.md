# Alexa Skill Setup Guide

## Overview

The NuVo MusicPort Alexa skill allows voice control of your multi-room audio system.

## Supported Commands

### Zone Power
- "Alexa, ask NuVo to turn on the living room"
- "Alexa, tell NuVo to turn off the master bedroom"

### Volume Control
- "Alexa, ask NuVo to set kitchen volume to 50"
- "Alexa, tell NuVo to volume up in the living room"
- "Alexa, ask NuVo to turn down the master bedroom"

### Mute
- "Alexa, ask NuVo to mute the living room"
- "Alexa, tell NuVo to unmute the kitchen"

### Source Selection
- "Alexa, ask NuVo to play music server A in the living room"

### System Commands
- "Alexa, ask NuVo to start party mode"
- "Alexa, tell NuVo to turn off all zones"

## Deployment Steps

### 1. Create AWS Lambda Function

```bash
cd alexa
pip install -r requirements.txt -t package/
cd package
zip -r ../function.zip .
cd ..
zip function.zip lambda_function.py
```

Upload to AWS Lambda:
- Runtime: Python 3.9
- Handler: lambda_function.lambda_handler
- Set environment variable: `NUVO_API_URL=http://your-server:8000`

### 2. Create Alexa Skill

1. Go to [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask)
2. Click "Create Skill"
3. Choose "Custom" model and "Provision your own" hosting
4. Upload `interaction_model.json` to the JSON Editor
5. Set endpoint to your Lambda ARN
6. Build the model

### 3. Link Lambda to Alexa

In Lambda:
- Add Alexa Skills Kit trigger
- Copy Skill ID from Alexa console
- Add to Lambda trigger configuration

### 4. Test

Use the Alexa Developer Console test tab:
- "open nuvo"
- "turn on the living room"

## Requirements

- AWS account with Lambda access
- Amazon Developer account
- API server accessible from internet (or use ngrok for testing)

## Configuration

Update zone and source names in:
- `interaction_model.json` - For voice recognition
- `lambda_function.py` - For zone name mapping

## Troubleshooting

Check CloudWatch Logs in AWS Lambda console for errors.
