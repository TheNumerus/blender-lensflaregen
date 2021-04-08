#define E 2.71828
#define PI 3.14159

float gauss(float x, float center, float std_dev) {
    return pow(E, -(pow(x - center, 2.0) / std_dev));
}