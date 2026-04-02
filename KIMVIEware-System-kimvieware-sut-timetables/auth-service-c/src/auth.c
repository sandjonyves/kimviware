/**
 * Authentication Service in C
 * Demonstrates branching for symbolic execution
 */
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>

#define MAX_USERNAME 50
#define MAX_PASSWORD 100
#define MIN_PASSWORD 8

typedef struct {
    char username[MAX_USERNAME];
    char password[MAX_PASSWORD];
    bool is_admin;
    int failed_attempts;
} User;

/**
 * Validate username
 * BRANCHES: 10+
 */
int validate_username(const char* username) {
    if (username == NULL) {
        return -1;
    }
    
    int len = strlen(username);
    
    if (len < 3) {
        return -2;
    }
    
    if (len > MAX_USERNAME - 1) {
        return -3;
    }
    
    if (!isalpha(username[0])) {
        return -4;
    }
    
    for (int i = 0; i < len; i++) {
        char c = username[i];
        
        if (!isalnum(c) && c != '_') {
            return -5;
        }
        
        if (c == '_' && i > 0 && username[i-1] == '_') {
            return -6;
        }
        
        if (c == '_' && i == len - 1) {
            return -7;
        }
    }
    
    if (strcmp(username, "admin") == 0 || 
        strcmp(username, "root") == 0 ||
        strcmp(username, "system") == 0) {
        return -8;
    }
    
    bool all_digits = true;
    for (int i = 0; i < len; i++) {
        if (!isdigit(username[i])) {
            all_digits = false;
            break;
        }
    }
    
    if (all_digits) {
        return -9;
    }
    
    return 0;
}

/**
 * Validate password strength
 * BRANCHES: 15+
 */
int validate_password(const char* password) {
    if (password == NULL) {
        return -1;
    }
    
    int len = strlen(password);
    
    if (len < MIN_PASSWORD) {
        return -2;
    }
    
    if (len > MAX_PASSWORD - 1) {
        return -3;
    }
    
    bool has_upper = false;
    bool has_lower = false;
    bool has_digit = false;
    bool has_special = false;
    
    for (int i = 0; i < len; i++) {
        char c = password[i];
        
        if (isupper(c)) {
            has_upper = true;
        } else if (islower(c)) {
            has_lower = true;
        } else if (isdigit(c)) {
            has_digit = true;
        } else if (c == '!' || c == '@' || c == '#' || 
                   c == '$' || c == '%' || c == '^' || 
                   c == '&' || c == '*') {
            has_special = true;
        } else {
            return -4;
        }
        
        if (i > 0 && password[i] == password[i-1]) {
            if (i > 1 && password[i] == password[i-2]) {
                return -5;
            }
        }
    }
    
    if (!has_upper) {
        return -8;
    }
    
    if (!has_lower) {
        return -9;
    }
    
    if (!has_digit) {
        return -10;
    }
    
    if (len >= 12) {
        if (!has_special) {
            return -11;
        }
    } else if (len >= 10) {
        if (!has_special) {
            int digit_count = 0;
            for (int i = 0; i < len; i++) {
                if (isdigit(password[i])) digit_count++;
            }
            if (digit_count < 3) {
                return -12;
            }
        }
    }
    
    const char* common[] = {
        "Password123", "Admin123", "Welcome123", 
        "Qwerty123", "Abc123456"
    };
    
    for (int i = 0; i < 5; i++) {
        if (strcmp(password, common[i]) == 0) {
            return -13;
        }
    }
    
    return 0;
}

/**
 * Authenticate user
 * BRANCHES: 20+
 */
int authenticate(const char* username, const char* password, 
                 User* users, int user_count, User** authenticated_user) {
    
    int username_valid = validate_username(username);
    if (username_valid != 0) {
        return username_valid;
    }
    
    int password_valid = validate_password(password);
    if (password_valid != 0) {
        return password_valid;
    }
    
    User* found_user = NULL;
    for (int i = 0; i < user_count; i++) {
        if (strcmp(users[i].username, username) == 0) {
            found_user = &users[i];
            break;
        }
    }
    
    if (found_user == NULL) {
        return -100;
    }
    
    if (found_user->failed_attempts >= 5) {
        return -101;
    }
    
    if (strcmp(found_user->password, password) != 0) {
        found_user->failed_attempts++;
        
        if (found_user->failed_attempts >= 5) {
            return -102;
        }
        
        return -103;
    }
    
    found_user->failed_attempts = 0;
    *authenticated_user = found_user;
    
    if (found_user->is_admin) {
        return 2;
    } else {
        return 1;
    }
}

/**
 * Register new user
 * BRANCHES: 15+
 */
int register_user(const char* username, const char* password,
                  User* users, int* user_count, int max_users) {
    
    int username_valid = validate_username(username);
    if (username_valid != 0) {
        return username_valid;
    }
    
    int password_valid = validate_password(password);
    if (password_valid != 0) {
        return password_valid;
    }
    
    if (*user_count >= max_users) {
        return -200;
    }
    
    for (int i = 0; i < *user_count; i++) {
        if (strcmp(users[i].username, username) == 0) {
            return -201;
        }
    }
    
    bool make_admin = (*user_count == 0);
    
    User* new_user = &users[*user_count];
    strncpy(new_user->username, username, MAX_USERNAME - 1);
    new_user->username[MAX_USERNAME - 1] = '\0';
    
    strncpy(new_user->password, password, MAX_PASSWORD - 1);
    new_user->password[MAX_PASSWORD - 1] = '\0';
    
    new_user->is_admin = make_admin;
    new_user->failed_attempts = 0;
    
    (*user_count)++;
    
    if (make_admin) {
        return 10;
    } else {
        return 11;
    }
}

/**
 * Change password
 * BRANCHES: 10+
 */
int change_password(User* user, const char* old_password, 
                    const char* new_password) {
    
    if (user == NULL || old_password == NULL || new_password == NULL) {
        return -1;
    }
    
    if (strcmp(user->password, old_password) != 0) {
        return -300;
    }
    
    if (strcmp(old_password, new_password) == 0) {
        return -301;
    }
    
    int new_valid = validate_password(new_password);
    if (new_valid != 0) {
        return new_valid;
    }
    
    strncpy(user->password, new_password, MAX_PASSWORD - 1);
    user->password[MAX_PASSWORD - 1] = '\0';
    
    return 0;
}

int main() {
    User users[100];
    int user_count = 0;
    
    printf("Auth Service - C Implementation\n");
    printf("Branches: ~60+ for symbolic execution\n");
    
    int result = register_user("alice", "SecurePass1!", users, &user_count, 100);
    printf("Register result: %d\n", result);
    
    User* auth_user = NULL;
    result = authenticate("alice", "SecurePass1!", users, user_count, &auth_user);
    printf("Auth result: %d\n", result);
    
    return 0;
}
