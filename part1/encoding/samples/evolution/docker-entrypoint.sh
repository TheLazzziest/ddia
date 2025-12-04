#!/bin/bash
set -e  # Exit on any error

# Suppress Python warnings (pkg_resources deprecation)
export PYTHONWARNINGS="ignore::UserWarning"

SCHEMAS_DIR="/app/schemas"
COMPILE_NEEDED=false

# Check if compilation is needed
for proto_file in "$SCHEMAS_DIR"/*.proto; do
    if [ -f "$proto_file" ]; then
        proto_name=$(basename "$proto_file" .proto)
        pb2_file="$SCHEMAS_DIR/${proto_name}_pb2.py"
        
        # Compile if _pb2.py doesn't exist or proto file is newer
        if [ ! -f "$pb2_file" ] || [ "$proto_file" -nt "$pb2_file" ]; then
            COMPILE_NEEDED=true
            break
        fi
    fi
done

if [ "$COMPILE_NEEDED" = true ]; then
    echo "🛠  Compiling Protobuf schemas..."
    
    # Find all .proto files and compile them
    for proto_file in "$SCHEMAS_DIR"/*.proto; do
        if [ -f "$proto_file" ]; then
            proto_name=$(basename "$proto_file" .proto)
            pb2_file="$SCHEMAS_DIR/${proto_name}_pb2.py"
            
            # Only compile if needed
            if [ ! -f "$pb2_file" ] || [ "$proto_file" -nt "$pb2_file" ]; then
                # Check if this is a gRPC service file
                if [ "$proto_name" = "person_service" ]; then
                    # Compile with gRPC support
                    python3 -W ignore::UserWarning -m grpc_tools.protoc \
                        -I"$SCHEMAS_DIR" \
                        --python_out="$SCHEMAS_DIR" \
                        --grpc_python_out="$SCHEMAS_DIR" \
                        "$proto_file" 2>/dev/null
                    
                    # Fix imports in generated files to use relative imports
                    if [ -f "$SCHEMAS_DIR/person_service_pb2.py" ]; then
                        sed -i 's/^import person_v\([12]\)_pb2 as \(.*\)/from . import person_v\1_pb2 as \2/' "$SCHEMAS_DIR/person_service_pb2.py"
                    fi
                    if [ -f "$SCHEMAS_DIR/person_service_pb2_grpc.py" ]; then
                        sed -i 's/^import person_service_pb2 as \(.*\)/from . import person_service_pb2 as \2/' "$SCHEMAS_DIR/person_service_pb2_grpc.py"
                        sed -i 's/^import person_v\([12]\)_pb2 as \(.*\)/from . import person_v\1_pb2 as \2/' "$SCHEMAS_DIR/person_service_pb2_grpc.py"
                    fi
                else
                    # Regular proto compilation
                    python3 -W ignore::UserWarning -m grpc_tools.protoc \
                        -I"$SCHEMAS_DIR" \
                        --python_out="$SCHEMAS_DIR" \
                        "$proto_file" 2>/dev/null
                fi
            fi
        fi
    done
    echo "✅ Schemas compiled"
fi

# Execute the command passed to the container (e.g., "python main.py 1")
exec "$@"