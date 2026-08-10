def payment_role_allowed(sess, allowed_roles):
    return sess.get("role") in allowed_roles
