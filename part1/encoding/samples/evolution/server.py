#!/usr/bin/env python3
"""gRPC Server for PersonService.

This server uses person_v2 schema to demonstrate schema evolution.
Clients using person_v1 can still interact with this server due to forward compatibility.
"""
import sys
import grpc
from concurrent import futures

# Import compiled gRPC modules
from schemas import person_service_pb2
from schemas import person_service_pb2_grpc
from schemas import person_v2_pb2


class PersonServiceServicer(person_service_pb2_grpc.PersonServiceServicer):
    """Implementation of PersonService using v2 schema."""
    
    def __init__(self):
        # In-memory storage using v2 schema
        self.persons = {}
        self.next_id = 1
    
    def CreatePerson(self, request, context):
        """Create a new person (accepts v1 or v2.Person due to forward compatibility)."""
        person_id = self.next_id
        self.next_id += 1
        
        # Convert request (which could be v1 or v2) to v2 for storage
        # Parse the serialized bytes to ensure compatibility
        person = person_v2_pb2.Person()
        person.ParseFromString(request.SerializeToString())
        person.id = person_id  # Assign server-generated ID
        
        # Ensure email field exists (if missing from v1, set empty string)
        if not person.email:
            person.email = ""
        
        self.persons[person_id] = person
        
        print(f"✅ Server: Created person ID={person_id}, name='{person.name}', email='{person.email}'")
        
        return person_service_pb2.PersonResponse(
            success=True,
            message=f"Person created successfully",
            person_id=person_id
        )
    
    def GetPerson(self, request, context):
        """Get person by ID (returns v2.Person)."""
        person_id = request.person_id
        
        if person_id not in self.persons:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Person with ID {person_id} not found")
            return person_v2_pb2.Person()
        
        person = self.persons[person_id]
        print(f"📤 Server: Sending person ID={person_id} (v2 schema)")
        return person
    
    def ListPersons(self, request, context):
        """List all persons (returns ListResponse with v2.Person)."""
        limit = request.limit if request.limit > 0 else len(self.persons)
        persons_list = list(self.persons.values())[:limit]
        
        print(f"📤 Server: Sending {len(persons_list)} persons (v2 schema)")
        
        return person_service_pb2.ListResponse(
            persons=persons_list,
            total=len(self.persons)
        )


def serve(port=50051):
    """Start the gRPC server."""
    print(f"🚀 Starting gRPC server on port {port}...")
    print(f"📋 Server is using person_v2 schema")
    print(f"🔌 Clients can connect using person_v1 or person_v2 (forward compatible)\n")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    person_service_pb2_grpc.add_PersonServiceServicer_to_server(
        PersonServiceServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"✅ Server is running on port {port}")
    print(f"⏳ Waiting for connections...\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop(0)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
    serve(port)

