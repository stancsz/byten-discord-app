# README

### Virtual Environment Setup

1. **Create**: Run `python -m venv venv` in your project directory.
2. **Activate**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Setup

1. **Build the Docker image**:
   ```bash
   docker build -t your-bot-name .
   ```

2. **Run the container**:
   ```bash
   docker run --env-file .env your-bot-name
   # or
   docker run -d --restart on-failure:3 --env-file .env your-bot-name
   ```

   Ensure you have a `.env` file containing the necessary environment variables, such as `DISCORD_BOT_TOKEN` and `SYSTEM_MESSAGE_URL`.


```
sudo su
docker stop $(docker ps -q)

docker build -t byten .
docker run -d --restart on-failure:3 --env-file .env byten
##
docker run --restart on-failure:3 --env-file .env byten
```