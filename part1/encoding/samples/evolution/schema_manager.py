import importlib
from pathlib import Path
from typing import Optional
from grpc_tools import protoc


class SchemaManager:
    
    def __init__(self, schemas_dir: str = "schemas"):
        self.schemas_dir = Path(schemas_dir).resolve()
        self._ensure_schemas_dir_exists()
    
    def _ensure_schemas_dir_exists(self):
        if not self.schemas_dir.exists():
            raise FileNotFoundError(f"Schemas directory not found: {self.schemas_dir}")
    
    def compile_all(self) -> bool:
        print("🛠  Compiling Protobuf schemas using grpcio-tools...")
        
        proto_files = list(self.schemas_dir.glob("*.proto"))
        
        if not proto_files:
            print(f"⚠️  No .proto files found in {self.schemas_dir}")
            return False
        
        success = True
        for proto_file in proto_files:
            if not self._compile_proto(proto_file):
                success = False
        
        return success
    
    def _compile_proto(self, proto_file: Path) -> bool:
        """Compile a single .proto file using grpcio-tools."""

        proto_file_str = str(proto_file.absolute())
        schemas_dir_str = str(self.schemas_dir.absolute())
        
        # Prepare command arguments
        args = [
            '',
            f'-I{schemas_dir_str}',
            f'--python_out={schemas_dir_str}',
            proto_file_str,
        ]
        
        try:
            # Call protoc.main() with arguments
            # It processes the args list similar to command line
            result_code = protoc.main(args)
            
            if result_code == 0:
                print(f"✅ Compiled {proto_file.name} successfully")
                return True
            else:
                print(f"❌ Error compiling {proto_file.name} (exit code: {result_code})")
                return False
                
        except SystemExit as e:
            # protoc.main() may raise SystemExit
            if e.code == 0:
                print(f"✅ Compiled {proto_file.name} successfully")
                return True
            else:
                print(f"❌ Error compiling {proto_file.name}")
                return False
        except Exception as e:
            print(f"❌ Error compiling {proto_file.name}: {e}")
            return False
    
    def load_module(self, module_name: str):
        module_path = f"{self.schemas_dir.name}.{module_name}_pb2"
        
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            print(f"❌ Could not import {module_path}: {e}")
            print(f"💡 Make sure schemas are compiled first!")
            raise
    
    def get_schema_version(self, module_name: str) -> Optional[str]:

        if '_v' in module_name:
            return module_name.split('_v')[1]
        return None


# Convenience functions for backward compatibility
_schema_manager = None

def get_manager(schemas_dir: str = "schemas") -> SchemaManager:
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaManager(schemas_dir)
    return _schema_manager

def compile_protos(schemas_dir: str = "schemas") -> bool:
    manager = get_manager(schemas_dir)
    return manager.compile_all()

def load_module(module_name: str, schemas_dir: str = "schemas"):
    manager = get_manager(schemas_dir)
    return manager.load_module(module_name)