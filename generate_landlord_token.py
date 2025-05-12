from auth_utils import create_jwt_token
from types import SimpleNamespace

# Mock landlord user object
landlord_user = SimpleNamespace(
    id="4124fc90-34fe-40d3-92bf-78e2d18a250c",
    email="landlord@example.com",
    role="landlord",
    community_id="00001"
)

token = create_jwt_token(landlord_user)
print(f"\n🔑 Valid landlord token:\n{token}\n")

