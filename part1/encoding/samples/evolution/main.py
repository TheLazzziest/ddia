import sys
import json
from schema_manager import compile_protos, load_module



def print_hex(data):
    """Pretty prints bytes in Hex format."""

    hex_str = " ".join(f"{b:02X}" for b in data)
    print(f"\n📦 Serialized Data (Hex):  [{hex_str}]")
    print(f"📊 Size: {len(data)} bytes\n")

def run_scenario_1():
    print("\n--- SCENARIO 1: The Basics ---")

    # 1. Load V1 Schema
    pb_v1 = load_module("person_v1")

    # 2. Create a Person object
    alice = pb_v1.Person(name="Alice", id=123)
    print(f"📝 Created Object (V1): {alice}")

    # 3. Serialize
    data = alice.SerializeToString()
    print_hex(data)

    # 4. Deserialize
    alice_decoded = pb_v1.Person()
    alice_decoded.ParseFromString(data)
    print(f"🔄 Deserialized Object: {alice_decoded}")
    assert alice.name == alice_decoded.name

def run_scenario_2():

    print("\n--- SCENARIO 2: Forward Compatibility (New Field) ---")
    print("Goal: Can Old Code (V1) read data written by New Code (V2)?")

    # Load schemas
    pb_v1 = load_module("person_v1")
    pb_v2 = load_module("person_v2")

    # 1. Write with V2 (New Code)
    bob_v2 = pb_v2.Person(name="Bob", id=456, email="bob@example.com")
    print(f"📝 Written by V2 (New): name='Bob', id=456, email='bob@example.com'")
    data = bob_v2.SerializeToString()
    print_hex(data)

    # 2. Read with V1 (Old Code)
    bob_v1 = pb_v1.Person()
    bob_v1.ParseFromString(data)
    
    print(f"🔄 Read by V1 (Old): {bob_v1}")
    print("✅ SUCCESS! V1 read the data without crashing. It just ignored the unknown 'email' field (tag 3).\n\n")
    print("📝 Note: The email field is NOT lost - it's still in the bytes. When Consumer V1 gets updated to V2, it will be able to read the email field. This is what makes Rolling Updates possible without downtime.")

def run_scenario_3():
    print("\n--- SCENARIO 3: Breaking Changes (Tag Reuse) ---")
    print("Goal: What happens if we reuse a Tag with a different type?")

    # Load schemas
    pb_v2 = load_module("person_v2")         # email is string (tag 3)
    pb_v3 = load_module("person_v3_broken")  # email is int32 (tag 3)

    # 1. Write with V2 (String)
    charlie_v2 = pb_v2.Person(name="Charlie", id=789, email="text_string")
    print(f"📝 Written by V2: email='text_string' (Tag 3, Type: String/WireType 2)")
    data = charlie_v2.SerializeToString()
    print_hex(data)

    # 2. Read with V3 (Int)
    print("💥 Attempting to read with V3 (Expects int32 at Tag 3)...")
    charlie_v3 = pb_v3.Person()
    
    try:
        charlie_v3.ParseFromString(data)
        print(f"Result object: {charlie_v3}")
        print(f"Value of 'email' field (int32): {charlie_v3.email}")
        
        if charlie_v3.email == 0:
             print("\n⚠️  DATA LOSS DETECTED! The parser ignored the field because types didn't match.")
             print("We sent a string, but the reader expected an int. The reader silently dropped the data.")

    except Exception as e:
        print(f"❌ CRASHED! Error: {e}")

def run_scenario_4():
    print("\n--- SCENARIO 4: Size Battle (JSON vs Protobuf) ---")
    print("Goal: Compare the memory footprint of JSON vs Protobuf encoding.")
    
    # Load schema
    pb_v2 = load_module("person_v2")
    
    # Create a person with realistic data
    person_proto = pb_v2.Person(
        name="Alexander Petrovich Ivanov",
        id=123456789,
        email="alexander.petrovich.ivanov@example-company.com"
    )
    
    # 1. Serialize to Protobuf
    proto_data = person_proto.SerializeToString()
    proto_size = len(proto_data)
    
    # 2. Create equivalent JSON dict and serialize
    person_json = {
        "name": "Alexander Petrovich Ivanov",
        "id": 123456789,
        "email": "alexander.petrovich.ivanov@example-company.com"
    }
    json_str = json.dumps(person_json)
    json_data = json_str.encode('utf-8')
    json_size = len(json_data)
    
    # 3. Compare
    print(f"\n📊 Person data:")
    print(f"   Name: {person_proto.name}")
    print(f"   ID: {person_proto.id}")
    print(f"   Email: {person_proto.email}")
    
    print(f"\n💾 JSON encoding:")
    print(f"   Size: {json_size} bytes")
    print(f"   Preview: {json_str[:60]}...")
    
    print(f"\n⚡ Protobuf encoding:")
    hex_str = " ".join(f"{b:02X}" for b in proto_data)
    print(f"   Size: {proto_size} bytes")
    print(f"   Hex: [{hex_str}]")
    
    # Calculate savings
    savings = json_size - proto_size
    savings_percent = (savings / json_size) * 100
    
    print(f"\n🎯 RESULT:")
    print(f"   Protobuf is {savings} bytes smaller ({savings_percent:.1f}% savings)!")
    print(f"   That's {json_size / proto_size:.1f}x more compact!")

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Usage: python main.py [1|2|3|4]")
        sys.exit(1)
        
    scenario = sys.argv[1]
    if scenario == "1":
        run_scenario_1()
    elif scenario == "2":
        run_scenario_2()
    elif scenario == "3":
        run_scenario_3()
    elif scenario == "4":
        run_scenario_4()
    else:
        print("Unknown scenario")