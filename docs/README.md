# Spatial AI Platform Documentation

This directory contains all documentation for the Spatial AI Platform project.

## Table of Contents

### Infrastructure & Deployment

- **[DOCKER_README.md](DOCKER_README.md)** - Docker setup and deployment guide
- **[MONGODB_SETUP.md](MONGODB_SETUP.md)** - MongoDB database configuration and setup
- **[MONGODB_VERIFICATION.md](MONGODB_VERIFICATION.md)** - MongoDB verification and testing procedures
- **[QUICK_START_MONGODB.md](QUICK_START_MONGODB.md)** - Quick start guide for MongoDB
- **[MINIO_SETUP.md](MINIO_SETUP.md)** - MinIO object storage configuration and setup
- **[MINIO_QUICK_START.md](MINIO_QUICK_START.md)** - MinIO quick start guide

### Frontend

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Frontend project structure and organization
- **[RTK_QUERY_GUIDE.md](RTK_QUERY_GUIDE.md)** - Redux Toolkit Query usage guide

### Implementation Tasks

- **[TASK_1.5_IMPLEMENTATION.md](TASK_1.5_IMPLEMENTATION.md)** - Task 1.5: MongoDB deployment implementation details

## Quick Links

### Getting Started

1. Start with [DOCKER_README.md](DOCKER_README.md) for overall deployment
2. Follow [QUICK_START_MONGODB.md](QUICK_START_MONGODB.md) to configure the database
3. Follow [MINIO_QUICK_START.md](MINIO_QUICK_START.md) to configure object storage
4. Review [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for frontend architecture

### Development

- Frontend state management: [RTK_QUERY_GUIDE.md](RTK_QUERY_GUIDE.md)
- Database verification: [MONGODB_VERIFICATION.md](MONGODB_VERIFICATION.md)

## Documentation Structure

```
docs/
├── README.md                      # This file
├── DOCKER_README.md               # Docker deployment
├── MONGODB_SETUP.md               # MongoDB configuration
├── MONGODB_VERIFICATION.md        # MongoDB testing
├── QUICK_START_MONGODB.md         # MongoDB quick start
├── MINIO_SETUP.md                 # MinIO configuration
├── MINIO_QUICK_START.md           # MinIO quick start
├── PROJECT_STRUCTURE.md           # Frontend structure
├── RTK_QUERY_GUIDE.md             # RTK Query guide
└── TASK_1.5_IMPLEMENTATION.md     # Implementation details
```

## Contributing

When adding new documentation:

1. Place all .md files in the `docs/` directory
2. Update this README.md with a link to the new document
3. Use clear, descriptive filenames in UPPERCASE with underscores
4. Include a table of contents in longer documents
5. Add code examples where appropriate

## Related Documentation

- **Spec Files**: `.kiro/specs/spatial-ai-platform/`
  - `requirements.md` - Platform requirements
  - `design.md` - System design and architecture
  - `tasks.md` - Implementation task list

## Support

For questions or issues:
- Check the relevant documentation file first
- Review the spec files in `.kiro/specs/spatial-ai-platform/`
- Consult the implementation task list in `tasks.md`
