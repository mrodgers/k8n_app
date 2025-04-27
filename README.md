# Kubernetes Python Application

A Python Flask application designed to run in Kubernetes or as a standalone container using Podman on macOS.

## Project Overview

This project demonstrates deploying a simple Python Flask application in a container environment. The application provides health check endpoints and demonstrates proper resource management, containerization, and deployment practices.

## Version Information

Current version: 1.0.0

This project follows [Semantic Versioning](https://semver.org/). Version numbers are in the format MAJOR.MINOR.PATCH, where:
- MAJOR version changes for incompatible API changes
- MINOR version changes for backward-compatible functionality additions
- PATCH version changes for backward-compatible bug fixes

## Current Architecture

The application is designed to run as:

1. A standalone container (recommended for macOS/Podman environments)
2. A Kubernetes deployment (for environments with full Kubernetes support)

### Architecture Details

The application follows a simple microservice architecture with the following components:

- **Web Layer**: Flask web application that handles HTTP requests
- **Business Logic Layer**: Core application logic implemented as Python modules
- **Health Monitoring**: Integrated health check system that reports application status
- **Logging System**: Structured logging that captures application events

The application is stateless, allowing for horizontal scaling in Kubernetes environments.

### Architecture Diagrams

Detailed architecture diagrams are available in the [docs/architecture.md](docs/architecture.md) file.

![High-Level Architecture](docs/images/high_level_architecture.png)

*Note: Architecture diagram images will be generated from the Mermaid diagrams during GitHub Pages setup.*

## Getting Started

### Prerequisites

- [Podman](https://podman.io/docs/installation) (v5.4.0 or later)
- Python 3.11+ (for local development)

### Directory Structure

```
.
├── app_manager.sh     # Main management script
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container definition
├── kubernetes/        # Kubernetes configuration
│   ├── deployment.yaml
│   └── service.yaml
├── src/               # Application source code
│   └── app.py         # Main Flask application
├── tests/             # Test files
├── logs/              # Log directory
└── archive/           # Archived scripts (for reference)
```

## Usage

The project provides a unified management script (`app_manager.sh`) that handles all aspects of building, deploying, and managing the application.

### Basic Commands

```bash
# Start the application
./app_manager.sh start

# Check application status
./app_manager.sh status

# Connect to the application (set up port forwarding)
./app_manager.sh connect

# View application logs
./app_manager.sh logs

# Stop the application
./app_manager.sh stop

# Clean up all resources
./app_manager.sh clean
```

### Advanced Usage

The management script supports additional options:

```bash
# Start with a specific port
./app_manager.sh start -p 8081

# Enable debug output
./app_manager.sh start -d

# Restart the application
./app_manager.sh restart
```

## macOS-Specific Considerations

When running on macOS with Podman, network isolation requires special handling. The `connect` command sets up the necessary port forwarding to enable access to the application.

## Kubernetes Configuration

The application includes Kubernetes manifests in the `kubernetes/` directory:

- `deployment.yaml`: Defines the application deployment with resource limits and health checks
- `service.yaml`: Creates a Kubernetes service to expose the application

## Health Checks

The application implements a health check endpoint at `/health` which returns a JSON response:

```json
{"status": "healthy"}
```

This endpoint is used by Kubernetes to ensure the application is running correctly.

## Configuration

The application can be configured using environment variables or a configuration file.

### Environment Variables

- `APP_PORT`: Port for the application to listen on (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO, options: DEBUG, INFO, WARNING, ERROR)
- `MAX_WORKERS`: Number of worker processes (default: 4)
- `ENV_MODE`: Application environment (default: production, options: development, testing, production)

### Configuration File

Alternatively, you can create a `config.yaml` file in the root directory with the following structure:

```yaml
app:
  port: 8080
  max_workers: 4
logging:
  level: INFO
environment: production
```

## Development

### Local Development

To run the application locally during development:

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   cd src
   python -m flask run --port=8080
   ```

### Running Tests

The project includes tests in the `tests/` directory:

```bash
pytest tests/
```

### Examples

#### Deploying to Production

```bash
# Build and deploy with production settings
./app_manager.sh start -e production

# Scale to 3 replicas in Kubernetes
./app_manager.sh scale 3
```

#### Development Workflow

```bash
# Start in development mode with live reloading
./app_manager.sh start -e development

# Run tests after code changes
pytest tests/

# Check logs for debugging
./app_manager.sh logs
```

## Troubleshooting

Common issues and their solutions:

1. **Port conflicts**: If port 8080 is already in use, the app_manager.sh script will attempt to find an available port automatically.

2. **Connection issues on macOS**: The `connect` command sets up SSH port forwarding to bridge the network isolation in Podman on macOS.

3. **Container startup problems**: Check the logs with `./app_manager.sh logs` to diagnose any issues with container startup.

4. **Performance issues**: If the application is running slowly, try increasing the `MAX_WORKERS` environment variable or adjust resource limits in the Kubernetes deployment.

5. **Configuration errors**: Verify your configuration settings by running `./app_manager.sh config-check`.

## Security Considerations

This application implements several security best practices:

1. **Container Security**: Running as a non-root user in the container
2. **Resource Limits**: Preventing resource exhaustion attacks
3. **Input Validation**: All API endpoints validate input data
4. **Dependency Management**: Regular updates of dependencies to address vulnerabilities
5. **Network Isolation**: Proper network configuration to limit exposure

### Security Recommendations

- Use TLS for production deployments
- Implement API authentication for protected endpoints
- Regularly update the base container image
- Follow the principle of least privilege for all service accounts

## Contributing

Contributions are welcome! Please check out our [contribution guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest enhancements.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

Copyright (c) 2025 [Project Owner]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.