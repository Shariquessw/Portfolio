# 1. Use a base image that has BOTH Python 3.11 and Node 20 installed
FROM nikolaik/python-nodejs:python3.11-nodejs20

# 2. Set the working directory inside the cloud server
WORKDIR /app

# 3. Copy all your files from GitHub into the server
COPY . .

# 4. Install your Node.js dependencies
RUN npm install

# 5. Install your Python dependencies (Update this list if your bots use other libraries!)
RUN pip3 install discord.py python-dotenv requests groq deep-translator flask google-genai

# 6. Expose the port your website runs on
EXPOSE 3000

# 7. Start the Mothership
CMD ["node", "server.js"]