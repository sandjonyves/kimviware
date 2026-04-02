# KIMVIEware System Under Test (SUT) - Timetables

This directory contains various implementations of a "Timetables" system, which serves as the System Under Test (SUT) for the KIMVIware platform. These services are the target for the analysis, test generation, and execution pipeline.

## Services

This SUT is composed of the following microservices:

*   **auth-service**: Authentication service (Python/Flask).
*   **auth-service-c**: Authentication service (C).
*   **auth-service-java**: Authentication service (Java/Spring Boot).
*   **course-service**: Service for managing courses.
*   **grade-service**: Service for managing grades.
*   **room-service**: Service for managing rooms.
*   **timetable-service**: The main service for managing timetables.

Each service is located in its own directory and contains the necessary files to run it independently. See the `README.md` file in each service's directory for specific instructions on how to run it.
