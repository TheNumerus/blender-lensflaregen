#define E 2.71828
#define PI 3.14159

float gauss(float x, float center, float std_dev) {
    return pow(E, -(pow(x - center, 2.0) / std_dev));
}

vec2 euler_to_polar(vec2 euler) {
    float dist = sqrt( pow(euler.x, 2.0) + pow(euler.y, 2.0) ); // [0.0; 1.0]

    // angle component of polar coordinates
    float angle = acos(euler.x / dist);
    if (euler.y < 0.0) {
        angle = -acos(euler.x / dist);
    }

    return vec2(dist, angle);
}