# Use a base image with BOTH Python and Node
FROM nikolaik/python-nodejs:python3.11-nodejs20

# Set the working directory
WORKDIR /app

# Copy all files into the server
COPY . .

# Install Node dependencies
RUN npm install

# Install Python dependencies
RUN pip3 install discord.py python-dotenv requests flask deep-translator google-genai groq

# Open the port
EXPOSE 3000

# Start the Mothership
CMD ["node", "server.js"]
