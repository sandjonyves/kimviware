
FROM amazoncorretto:17-alpine
WORKDIR /app
# Installation de curl pour le test de santé (healthcheck)
RUN apk add --no-cache curl
# Copie des sources
COPY . .
# Compilation directe du fichier unique et de son wrapper web
RUN javac src/main/java/com/kimvieware/auth/AuthService.java src/main/java/com/kimvieware/auth/WebAuthService.java
# Exposition du port
EXPOSE 8081
# Lancement du service web
CMD ["java", "-cp", "src/main/java", "com.kimvieware.auth.WebAuthService"]
