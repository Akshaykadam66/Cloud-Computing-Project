## Ride-Share 
An application that allows user to create a ride or share a ride by renting out bike/cabs.\
**The user can perform the following tasks**
  * Creating a ride.                                                                                   
  * Sharing a already created ride.
  * Manipulate the existing rides.
  
 ### Tools and Technology
  * **Programming Language** - Python
  * **Framework** - Flask, to implement API endpoints
  * **Back-End Architecture** - Master-Slave 
  * **RabbitMQ** - A message broker software used for communication between different components.
  * **Docker-Container**  - To implement microservices, and to isolate the applications
  * **Database** - SQLite3

  ### Features of the application
  
  * **Scalability** Auto scaling of docker-containers based on the traffic/requests.
  * **High Availability** If a slave worker fails,a new slave worker is started. All the data is copied to the new slave. asynchronously.

>the future enhancement of this project can include features like online-mode payment. there no 
>GUI developed for this particular project, the communication can happen through API testing tool
>postman the requests made to the application will gracfully handled by the API in the background!
  
