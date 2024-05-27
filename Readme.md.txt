After Installaing Kubernetes Mount The Volumes for minkube for testing purpose:
minikube start --mount --mount-string="C:\\Users\\Lenovo\\Desktop\\Deployment\\host-custom:/mnt/host-custom"

# Set Docker context to a valid one (replace 'default' with a valid context if 'default' isn't listed)
docker context use default

Deployments in Kubernetes serve several important purposes that make managing and scaling containerized applications more efficient and reliable

Servicesin Kubernetes serve several important purposes that Exposing the Applications: A Service provides a stable endpoint (an IP address and port) and for external access out of the claster 

 Managing The Volume and the storage and the access