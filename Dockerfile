FROM python:3.7-alpine

RUN apk add --no-cache gcc

RUN apk add libc-dev

# Create app directory
WORKDIR /app

# Install app dependencies
COPY ./requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY src /app

EXPOSE 5000
CMD [ "python", "controller.py" ]
