# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

RUN poetry run playwright install-deps

RUN poetry run playwright install chromium

COPY . /app

# Expose the port your application listens on (if applicable)
EXPOSE 8001

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Define the command to run your application
CMD ["poetry", "run", "uvicorn", "src.endpoint:app", "--host", "0.0.0.0", "--reload"]