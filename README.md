# Music Recommender : CS310 Final Project
## How to Install
### Database
1. Run create-db.sql to create the database and tables.
2. Add your database endpoint, port number, region, username, user pwd, and db name to the musicapp-config.ini file under rds section.
### S3
1. Create a bucket for the app. Add bucketname and regionname to config file under s3 section.
2. add a s3readonly and s3readwrite section to config file with regionname, accessid and accesskey.
### HuggingFace
Get a Hugging Face API key and add it to the config file under hf section.
### Spotify
Add your clientid and clientsecret to the config file under spotify section.
Since Spotify isn't actually called, you can use placeholder values.
### Lambda
1. Create lambda functions for all the final-project*.py files with Python 3.13 on x64 runtime.
2. Modify the functions to have a larger memory and longer execution time.
3. Pip install the required imports and create a layer. Add the layer to all functions.
4. Add datatier.py, musicapp-config.ini to every lambda function.
5. Add emotion.py to the lamnda functions with final-project-image-analysis.py, and final-project-text-analysis.py.
6. Add spotify.py to the lambda function with final-project-songrec.py.
7. Set up API Gateway as described in the project description and deploy.
### Client-side
1. Add the webservice (API Gateway) endpoint to the musicapp-client-config.ini file under client section.