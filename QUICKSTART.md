# Quick Start Guide

Get your LLM Inference Platform running in minutes!

## 🚀 Option 1: Docker Compose (Easiest)

### Prerequisites
- Docker Desktop installed and running
- 8GB+ RAM available

### Steps

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for services to start** (about 30 seconds):
   ```bash
   docker-compose ps
   ```

3. **Open web browser:**
   ```
   http://localhost:8000
   ```

4. **Start using the LLM!**
   - Type your prompt in the text area
   - Adjust settings (max tokens, temperature)
   - Click "Generate Response"

### Stop Services

```bash
docker-compose down
```

---

## 🛠️ Option 2: Local Development

### Prerequisites
- Python 3.9+
- Docker Desktop (for Kafka)

### Steps

1. **Start Kafka:**
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. **Start Worker** (Terminal 1):
   ```bash
   cd worker
   pip install -r requirements.txt
   python -m worker.main
   ```

3. **Start Web Frontend** (Terminal 2):
   ```bash
   cd web
   pip install -r requirements.txt
   python -m web.main
   ```

4. **Open browser:**
   ```
   http://localhost:8000
   ```

---

## 📝 Using the Web Interface

1. **Enter a prompt** in the text area
   - Example: "What is machine learning?"
   - Example: "Write a short story about AI"

2. **Adjust settings** (optional):
   - **Max Tokens**: Maximum length of response (50-1024)
   - **Temperature**: Creativity level (0.0-2.0)
     - Lower = more focused
     - Higher = more creative

3. **Click "Generate Response"**

4. **View results**:
   - Generated text appears below
   - See response time and token count
   - Request ID for tracking

---

## 🔧 Troubleshooting

### Services won't start

**Check Docker:**
```bash
docker ps
docker-compose ps
```

**Check logs:**
```bash
docker-compose logs
docker-compose logs worker
docker-compose logs web
```

### Web UI shows "Connection Error"

1. **Verify Kafka is running:**
   ```bash
   docker ps | grep kafka
   ```

2. **Verify Worker is running:**
   ```bash
   curl http://localhost:8081/health
   ```

3. **Check environment variables:**
   - Web frontend needs: `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`
   - Worker needs: `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`

### Model loading is slow

- First run downloads the model (can take several minutes)
- Subsequent runs are faster (model is cached)
- For faster startup, use smaller models like `TinyLlama/TinyLlama-1.1B-Chat-v1.0`

### Out of memory errors

- Reduce `BATCH_SIZE` in worker config
- Use CPU instead of GPU: `MODEL_DEVICE=cpu`
- Use smaller model: `MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0`

---

## 🎯 Next Steps

- **Deploy to Azure**: See deployment guides
- **Customize Model**: Change `MODEL_NAME` environment variable
- **Scale Workers**: Add more worker instances for higher throughput
- **Monitor**: Check metrics at http://localhost:8080/metrics

---

## 💡 Tips

- **Better prompts = better results**: Be specific and clear
- **Temperature 0.7-0.9**: Good balance for most tasks
- **Max tokens 256-512**: Usually sufficient for most responses
- **Use Ctrl+Enter**: Quick submit in the text area

---

## 📞 Support

- Check logs: `docker-compose logs`
- Health checks: http://localhost:8000/health
- Worker health: http://localhost:8081/health
