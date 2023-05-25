
FROM python:3.9.16-alpine
# Create app directory
WORKDIR /queencubator
# Copy necessary files to image
COPY	 . .
# Upgrade pip and install dependencies
RUN	pip3 install --upgrade pip && \
	pip3 install -r requirements.txt
