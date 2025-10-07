"""Public Service Navigator"""

import from byllm.llm { Model }

glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);

def find_services(country: str, service: str, city: str) -> str by llm();
def get_guidance(country: str, service: str, city: str) -> str by llm();

walker main {
    with entry {
        print("PUBLIC SERVICE NAVIGATOR");
        
        search_again = "yes";
        
        while search_again == "yes" {
            print("==========================================");
            
            country = input("Enter country: ");
            service_type = input("Service needed: ");
            city = input("Enter city: ");
            
            print("Searching for services...");
            
            services = find_services(country, service_type, city);
            guidance = get_guidance(country, service_type, city);
            
            print("==========================================");
            print("SERVICE RECOMMENDATIONS");
            print("==========================================");
            print("Location: " + city + ", " + country);
            print("Service: " + service_type);
            print("OFFICES:");
            print(services);
            print("GUIDANCE:");
            print(guidance);
            print("==========================================");
            
            search_again = input("Find another service? (yes/no): ");
        }
        
        print("Thank you!");
    }
}