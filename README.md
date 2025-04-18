# TS Metrics Analyzer

A metrics analysis tool for code repositories, focusing on code quality and risk assessment across multiple programming languages.

## Features

- Language-agnostic code analysis using Lizard library
- Comprehensive metrics tracking (LOC, complexity, nesting, etc.)
- Binary classification system for code quality
- Support for multiple programming languages
- Repository analysis with detailed metrics

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Running with Docker Compose

1. Clone this repository:
   ```
   git clone https://github.com/your-username/ts-metrics-analyzer.git
   cd ts-metrics-analyzer
   ```

2. Build and start the containers:
   ```
   docker-compose up -d
   ```

3. The API will be available at:
   ```
   http://localhost:5001
   ```

4. To stop the containers:
   ```
   docker-compose down
   ```

## API Usage

### Analyze Repository

**Endpoint:** `POST /analyze`

**Request Body:**
```json
{
  "repo": "https://github.com/username/repository",
  "branch": "main",
  "token": "your_github_token"  // Optional
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "repository-name",
  "organizationId": "uuid",
  "branchId": "uuid",
  "link": "https://github.com/organization/repository/",
  "authors": [
    {
      "id": "uuid",
      "name": "Author Name",
      "link": "https://github.com/author"
    }
  ],
  "commits": [
    {
      "commitId": "uuid",
      "authorId": "uuid",
      "branchId": "uuid",
      "repositoryId": "uuid",
      "autor": "Author Name",
      "link": "https://github.com/organization/repository/commit/sha",
      "sha": "commit-sha",
      "createAt": "timestamp",
      "message": "commit message",
      "filePath": "path/to/file",
      "changeCode": "code diff",
      "risk": 2,
      "riskComment": "Risk assessment comment",
      "quality": 5,
      "qualityComment": "Quality assessment comment",
      "metrics": {
        "loc": 100,
        "wmc": 5,
        "rfc": 10,
        "cbo": 3,
        "dit": 1,
        "nosi": 0,
        "loopQty": 2,
        "comparisonsQty": 15,
        "variablesQty": 8,
        "maxNestedBlocks": 2
      }
    }
  ]
}
```

## Development Setup

If you prefer to run the application without Docker:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python run.py
   ```

## License

[MIT](LICENSE)
