package com.kimvieware.auth;

import java.util.*;
import java.util.regex.*;

/**
 * Authentication Service in Java
 * Demonstrates branching for symbolic execution
 */
public class AuthService {
    
    private static final int MIN_USERNAME_LENGTH = 3;
    private static final int MAX_USERNAME_LENGTH = 50;
    private static final int MIN_PASSWORD_LENGTH = 8;
    private static final int MAX_PASSWORD_LENGTH = 100;
    private static final int MAX_FAILED_ATTEMPTS = 5;
    
    private Map<String, User> users = new HashMap<>();
    
    /**
     * User class
     */
    public static class User {
        private String username;
        private String password;
        private boolean isAdmin;
        private int failedAttempts;
        
        public User(String username, String password, boolean isAdmin) {
            this.username = username;
            this.password = password;
            this.isAdmin = isAdmin;
            this.failedAttempts = 0;
        }
        
        public String getUsername() { return username; }
        public String getPassword() { return password; }
        public boolean isAdmin() { return isAdmin; }
        public int getFailedAttempts() { return failedAttempts; }
        public void setPassword(String password) { this.password = password; }
        public void incrementFailedAttempts() { this.failedAttempts++; }
        public void resetFailedAttempts() { this.failedAttempts = 0; }
    }
    
    /**
     * Validate username
     * BRANCHES: 15+
     */
    public String validateUsername(String username) {
        // Branch 1: Null check
        if (username == null) {
            return "Username cannot be null";
        }
        
        // Branch 2: Empty check
        if (username.isEmpty()) {
            return "Username cannot be empty";
        }
        
        // Branch 3: Minimum length
        if (username.length() < MIN_USERNAME_LENGTH) {
            return "Username too short (minimum " + MIN_USERNAME_LENGTH + " characters)";
        }
        
        // Branch 4: Maximum length
        if (username.length() > MAX_USERNAME_LENGTH) {
            return "Username too long (maximum " + MAX_USERNAME_LENGTH + " characters)";
        }
        
        // Branch 5: First character must be letter
        if (!Character.isLetter(username.charAt(0))) {
            return "Username must start with a letter";
        }
        
        // Branch 6-8: Character validation
        for (int i = 0; i < username.length(); i++) {
            char c = username.charAt(i);
            
            // Only alphanumeric and underscore
            if (!Character.isLetterOrDigit(c) && c != '_') {
                return "Username can only contain letters, digits, and underscores";
            }
            
            // No consecutive underscores
            if (c == '_' && i > 0 && username.charAt(i - 1) == '_') {
                return "Username cannot have consecutive underscores";
            }
            
            // No underscore at end
            if (c == '_' && i == username.length() - 1) {
                return "Username cannot end with underscore";
            }
        }
        
        // Branch 9: Reserved usernames
        Set<String> reserved = new HashSet<>(Arrays.asList("admin", "root", "system", "guest"));
        if (reserved.contains(username.toLowerCase())) {
            return "Username is reserved";
        }
        
        // Branch 10: All digits check
        boolean allDigits = true;
        for (char c : username.toCharArray()) {
            if (!Character.isDigit(c)) {
                allDigits = false;
                break;
            }
        }
        
        if (allDigits) {
            return "Username cannot be all digits";
        }
        
        return null; // Valid
    }
    
    /**
     * Validate password strength
     * BRANCHES: 20+
     */
    public String validatePassword(String password) {
        // Branch 1: Null check
        if (password == null) {
            return "Password cannot be null";
        }
        
        // Branch 2: Empty check
        if (password.isEmpty()) {
            return "Password cannot be empty";
        }
        
        // Branch 3: Minimum length
        if (password.length() < MIN_PASSWORD_LENGTH) {
            return "Password too short (minimum " + MIN_PASSWORD_LENGTH + " characters)";
        }
        
        // Branch 4: Maximum length
        if (password.length() > MAX_PASSWORD_LENGTH) {
            return "Password too long (maximum " + MAX_PASSWORD_LENGTH + " characters)";
        }
        
        // Password strength checks
        boolean hasUpper = false;
        boolean hasLower = false;
        boolean hasDigit = false;
        boolean hasSpecial = false;
        
        String specialChars = "!@#$%^&*()_+-=[]{}|;:,.<>?";
        
        // Branch 5-9: Character type detection
        for (int i = 0; i < password.length(); i++) {
            char c = password.charAt(i);
            
            if (Character.isUpperCase(c)) {
                hasUpper = true;
            } else if (Character.isLowerCase(c)) {
                hasLower = true;
            } else if (Character.isDigit(c)) {
                hasDigit = true;
            } else if (specialChars.indexOf(c) != -1) {
                hasSpecial = true;
            } else {
                return "Password contains invalid character: " + c;
            }
            
            // Branch: No consecutive identical characters
            if (i > 0 && password.charAt(i) == password.charAt(i - 1)) {
                if (i > 1 && password.charAt(i) == password.charAt(i - 2)) {
                    return "Password cannot have three consecutive identical characters";
                }
            }
        }
        
        // Branch 10: Must have uppercase
        if (!hasUpper) {
            return "Password must contain at least one uppercase letter";
        }
        
        // Branch 11: Must have lowercase
        if (!hasLower) {
            return "Password must contain at least one lowercase letter";
        }
        
        // Branch 12: Must have digit
        if (!hasDigit) {
            return "Password must contain at least one digit";
        }
        
        // Branch 13-14: Special character requirements based on length
        if (password.length() >= 12) {
            if (!hasSpecial) {
                return "Passwords 12+ characters must contain a special character";
            }
        } else if (password.length() >= 10) {
            if (!hasSpecial) {
                // Count digits
                int digitCount = 0;
                for (char c : password.toCharArray()) {
                    if (Character.isDigit(c)) digitCount++;
                }
                if (digitCount < 3) {
                    return "Passwords 10-11 characters need special char OR 3+ digits";
                }
            }
        }
        
        // Branch 15: Common password check
        Set<String> common = new HashSet<>(Arrays.asList(
            "Password123", "Admin123", "Welcome123", "Qwerty123"
        ));
        if (common.contains(password)) {
            return "Password is too common";
        }
        
        // Branch 16: Sequential characters
        for (int i = 0; i < password.length() - 2; i++) {
            if (password.charAt(i) + 1 == password.charAt(i + 1) &&
                password.charAt(i) + 2 == password.charAt(i + 2)) {
                return "Password cannot contain sequential characters (abc, 123)";
            }
        }
        
        return null; // Valid
    }
    
    /**
     * Register new user
     * BRANCHES: 15+
     */
    public String registerUser(String username, String password) {
        // Branch 1-2: Validate username
        String usernameError = validateUsername(username);
        if (usernameError != null) {
            return usernameError;
        }
        
        // Branch 3-4: Validate password
        String passwordError = validatePassword(password);
        if (passwordError != null) {
            return passwordError;
        }
        
        // Branch 5: Check if username exists
        if (users.containsKey(username)) {
            return "Username already exists";
        }
        
        // Branch 6-7: First user is admin
        boolean isAdmin = users.isEmpty();
        
        // Create user
        User user = new User(username, password, isAdmin);
        users.put(username, user);
        
        // Branch 8: Return appropriate message
        if (isAdmin) {
            return "ADMIN_CREATED";
        } else {
            return "USER_CREATED";
        }
    }
    
    /**
     * Authenticate user
     * BRANCHES: 20+
     */
    public String authenticate(String username, String password) {
        // Branch 1-2: Validate inputs
        String usernameError = validateUsername(username);
        if (usernameError != null) {
            return "INVALID_USERNAME";
        }
        
        String passwordError = validatePassword(password);
        if (passwordError != null) {
            return "INVALID_PASSWORD";
        }
        
        // Branch 3: Check if user exists
        if (!users.containsKey(username)) {
            return "USER_NOT_FOUND";
        }
        
        User user = users.get(username);
        
        // Branch 4: Check if account is locked
        if (user.getFailedAttempts() >= MAX_FAILED_ATTEMPTS) {
            return "ACCOUNT_LOCKED";
        }
        
        // Branch 5-7: Check password
        if (!user.getPassword().equals(password)) {
            user.incrementFailedAttempts();
            
            // Branch: Lock account after max attempts
            if (user.getFailedAttempts() >= MAX_FAILED_ATTEMPTS) {
                return "ACCOUNT_LOCKED_NOW";
            }
            
            return "WRONG_PASSWORD";
        }
        
        // Branch 8: Success - reset failed attempts
        user.resetFailedAttempts();
        
        // Branch 9-10: Admin vs regular user
        if (user.isAdmin()) {
            return "ADMIN_AUTHENTICATED";
        } else {
            return "USER_AUTHENTICATED";
        }
    }
    
    /**
     * Change password
     * BRANCHES: 10+
     */
    public String changePassword(String username, String oldPassword, String newPassword) {
        // Branch 1: User exists
        if (!users.containsKey(username)) {
            return "USER_NOT_FOUND";
        }
        
        User user = users.get(username);
        
        // Branch 2: Verify old password
        if (!user.getPassword().equals(oldPassword)) {
            return "WRONG_OLD_PASSWORD";
        }
        
        // Branch 3: New password different from old
        if (oldPassword.equals(newPassword)) {
            return "NEW_PASSWORD_SAME_AS_OLD";
        }
        
        // Branch 4-5: Validate new password
        String passwordError = validatePassword(newPassword);
        if (passwordError != null) {
            return passwordError;
        }
        
        // Branch 6: Update password
        user.setPassword(newPassword);
        
        return "PASSWORD_CHANGED";
    }
    
    /**
     * Main method for testing
     */
    public static void main(String[] args) {
        System.out.println("Auth Service - Java Implementation");
        System.out.println("Branches: ~80+ for symbolic execution");
        System.out.println();
        
        AuthService service = new AuthService();
        
        // Test registration
        String result = service.registerUser("alice", "SecurePass1!");
        System.out.println("Register result: " + result);
        
        // Test authentication
        result = service.authenticate("alice", "SecurePass1!");
        System.out.println("Auth result: " + result);
        
        // Test invalid password
        result = service.authenticate("alice", "WrongPass");
        System.out.println("Wrong password: " + result);
    }
}
