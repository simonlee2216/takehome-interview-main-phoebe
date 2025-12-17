# Project Reflection

For this take home project, I implemented a small-scaled fanout service utilizing the provided sample data, so that it can notify caregivers about open shifts to accept the claim and then escalating the notifications if no caregiver takes it after 10 minutes. The objective of this project was to create a service where the fastapi can handle concurrent requests in a safe manner while respecting idempotency and correctly assigning shifts. I made design decisions that balanced simplicity, readability, and concurrency safety, while keeping the in-memory database approach for speed and ease of testing.

## app/database.py

**InMemoryKeyValueDatabase**  
Used as the base class and further added a ‘Registry’ class to add helper methods for the shifts and caregivers allowing for better readability and keeping key formatting and logic separate from each other.  
- I added a universal find method to allow searching items by any predicate, which simplifies filtering logic and avoids repetitive loops throughout the code. This made it easy to implement domain-specific queries later.  
- This design favors clarity and maintainability over raw performance, which would matter more with a larger dataset.

**Registry subclass**  
This class extends the base class as it provides helper functions for both shifts and caregivers.  
- **Shifts**: get_shift and save_shift handle how shift data is stored and retrieved in the database, so other parts of the code don’t have to worry about formatting the keys or details of storage.  
- **Caregivers**: get_caregiver, save_caregiver, get_caregiver_phone, and get_caregivers_role make it easy to look up caregivers by ID, phone number, or role without needing to manually search through the database each time.  
    - get_caregiver_phone and get_caregivers_role are specifically designed to allow the service to identify incoming messages and notify the right caregivers for a shift.  
- Given the small-scale nature of this project, the simplification of the logic is more beneficial.  
Using these helper methods ensures that shifts and caregivers are always saved with a consistent key format (like shift:{id} or caregiver:{id}), which prevents accidentally overwriting or mixing up data.

**Load_data**  
This function reads from the sample_data.json and initializes the shifts and caregivers by adding default attributes (status = "OPEN", fanout_started = False, and assigned_caregiver_id = None) to ensure all shifts start at a consistent state.  
- Logging was added to show how many shifts and caregivers were added.  
- It is synchronous for simplicity but for larger datasets would most likely require async loading or batching.

## app/fanout_service.py

**Notify_caregivers**  
This function sends out notifications for a shift. It firstly checks if the shift is existent (OPEN) and also checks if it hasn’t been sent out yet already to avoid duplicates.  
- Marks fanout_started as true if notifications have been sent.  
- Sends sms to the caregivers who have a role that is the same as the role required for the shift.  
- It then adds a task using BackgroundTasks to run call_unclaimed so that after 10 minutes to call caregivers if no one claims the shift. Using BackgroundTasks allows for other tasks to run while waiting for the 10 minutes.  
Checking for shift existence, status, and fanout_started allows for safety and idempotency.

**Call_unclaimed**  
This function handles the case where after a first round of notifications that have been sent out, the shift is still unclaimed and has to send out another round.  
- Checking if shift still exists and is OPEN preventing unnecessary calls if the shift has already been called.  
- Uses a lock (get_shift_lock) to prevent race conditions while sending calls and updating the shift status.  
    - Locks maintain secure and consistent shift handling ensuring notifications are sent to the correct caregivers and separates from the main fanout process so that there is a continuous response and non-blocking.  
    - The lock is per-shift rather than global, which is efficient for this service but assumes only one instance of the microservice is running, which is okay.

**process_reply**  
Handles inbound messages from caregivers who want to claim a shift and safely assigns shifts.  
- Uses the phone number from the message using get_caregiver_phone to determine which caregiver is sending the request.  
- Uses a lock to safely assign the shift to the first caregiver who responds.  
- Updates the shift status to FILLED and stores the assigned caregiver ID.  
- Sends confirmation or error messages back to the caregiver.  
This logic guarantees that each shift is assigned to exactly one caregiver, even if multiple responses arrive nearly simultaneously.  
- Messages are parsed with basic yes or accept indicating acceptance which is acceptable for this project but other edge cases would require more complex parsing.

## app/api.py

This module sets up the FastAPI application and exposes the public API endpoints for the fanout service.

- **Load_data**: The sample data is loaded at startup by load_data and allows for the in-memory database to be fully ready before requests are processed.  
- **Health_check**: Provides a simple GET endpoint to verify that the service is running.  
- **fanout**: POST endpoint that sends notifications for a shift. It uses BackgroundTasks so follow-up calls can run in the background without blocking the request.  
- **Inbound**: POST endpoint for incoming SMS or calls. Messages are then passed to process_reply to safely assign shifts to caregivers.  
- **Create_app**: This function creates the fastapi app and adds the router so the endpoints function as expected.  

## Conclusion

Overall, this project was a great exercise in building a small-scale, concurrent service that is both safe and responsive. By leveraging fastapi’s BackgroundTasks, I was able to ensure that shift notifications and follow-ups could run asynchronously without blocking the server, keeping the application responsive even during the 10-minute time limit. I prioritized code readability and maintainability by separating content, such as isolating database logic in the Registry class and moving business logic to the fanout service. This structure made the service easier to understand, debug, and extend, while still achieving the core functionality of reliably assigning shifts to caregivers. The project reinforced the importance of balancing concurrency, simplicity, and clarity in implementation.

## Use of LLM tools

During this project, I used AI tools primarily for guidance on code organization and design decisions. I consulted the model for advice on separating the API layer from the fanout service, structuring helper methods in the Registry class for clarity and reusability, and deciding where to place load_data to ensure the in-memory database is initialized properly. I also sought clarification on FastAPI async patterns, BackgroundTasks, and concurrency considerations. While the AI provided reference, suggestions, and brainstorming support, all coding, implementation, and final design decisions, the fanout logic, locks, and API endpoints, were completed by me. The tools helped refine certain aspects, but they did not generate the full solution.
