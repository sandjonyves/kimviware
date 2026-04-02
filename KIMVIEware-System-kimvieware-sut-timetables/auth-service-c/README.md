# Auth Service (C)

This is an authentication service implemented in C, designed for symbolic execution testing.

## Prerequisites

*   A C compiler, such as `clang` or `gcc`.
*   `make`

## Build

To build the service, run the following command from this directory:

```bash
make
```

This will create an executable file named `auth_service`.

## Usage

To run the service, execute the following command:

```bash
./auth_service
```

## Features

*   Username validation (10+ branches)
*   Password strength validation (15+ branches)
*   User authentication (20+ branches)
*   User registration (15+ branches)
*   Password change (10+ branches)

**Total**: ~70 branches, which can lead to over 100 paths with symbolic execution.

## Symbolic Execution

*   **Expected paths**: 80-120 execution paths
*   This service is a good example of path explosion in C code.
