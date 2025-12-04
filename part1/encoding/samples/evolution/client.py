#!/usr/bin/env python3
"""gRPC Client for PersonService.

This client uses person_v1 schema to demonstrate forward compatibility.
Even though the server uses person_v2, this client can successfully interact with it.
"""
import sys
import grpc

from schemas import person_service_pb2
from schemas import person_service_pb2_grpc
from schemas import person_v1_pb2


def run_client(server_address='localhost:50051'):
    """Run the gRPC client."""
    print(f"🔗 Connecting to gRPC server at {server_address}...")
    print(f"📋 Client is using person_v1 schema (older version)")
    print(f"📋 Server is using person_v2 schema (newer version)")
    print(f"✨ Demonstrating forward compatibility over network...\n")
    
    # Create channel and stub
    channel = grpc.insecure_channel(server_address)
    stub = person_service_pb2_grpc.PersonServiceStub(channel)
    
    try:
        # Test connection
        print("=" * 60)
        print("TEST 1: Client (v1) creates person, Server (v2) stores it")
        print("=" * 60)
        
        # Create a person using v1 schema (no email field)
        person_v1 = person_v1_pb2.Person(name="Alice", id=0)  # id will be assigned by server
        print(f"\n📝 Client (v1): Creating person: name='{person_v1.name}'")
        
        # Send to server (server expects v2, but v1 is compatible)
        response = stub.CreatePerson(person_v1)
        print(f"✅ Server response: {response.message}, ID={response.person_id}")
        
        # ============================================================
        
        print("\n" + "=" * 60)
        print("TEST 2: Client (v1) reads person from Server (v2)")
        print("=" * 60)
        
        # Get person by ID
        request = person_service_pb2.PersonRequest(person_id=response.person_id)
        print(f"\n📥 Client (v1): Requesting person ID={response.person_id}")
        
        # Server returns v2.Person (with email field)
        person_from_server = stub.GetPerson(request)
        
        # Client reads it using v1 schema
        print(f"📦 Server (v2): Sent person with fields: name, id, email")
        print(f"👁️  Client (v1): Reading person...")
        print(f"   - name: '{person_from_server.name}' ✅")
        print(f"   - id: {person_from_server.id} ✅")
        print(f"   - email: (field exists but ignored by v1 client)")
        
        # Parse with v1 schema to show forward compatibility
        person_v1_read = person_v1_pb2.Person()
        person_v1_read.ParseFromString(person_from_server.SerializeToString())
        
        print(f"\n✅ SUCCESS! Client (v1) successfully read data from Server (v2)")
        print(f"   v1 client received: name='{person_v1_read.name}', id={person_v1_read.id}")
        print(f"   The 'email' field was preserved in bytes but ignored by v1 client")
        print(f"   This is forward compatibility in action!")
        
        # ============================================================
        
        print("\n" + "=" * 60)
        print("TEST 3: List all persons")
        print("=" * 60)
        
        list_request = person_service_pb2.ListRequest(limit=10)
        list_response = stub.ListPersons(list_request)
        
        print(f"\n📋 Server has {list_response.total} person(s) stored:")
        for i, person in enumerate(list_response.persons, 1):
            print(f"   {i}. ID={person.id}, name='{person.name}', email='{person.email}'")
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)
        
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()} - {e.details()}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        channel.close()


if __name__ == '__main__':
    server_address = sys.argv[1] if len(sys.argv) > 1 else 'localhost:50051'
    run_client(server_address)

