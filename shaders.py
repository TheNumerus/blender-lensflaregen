# language=GLSL
vertex_shader_ghost = '''
    uniform mat4 modelMatrix;
    uniform mat4 rotationMatrix;
    uniform float aspect_ratio;

    in vec2 position;
    in vec4 vertColor;

    out vec2 posInterp;
    out vec4 colorInterp;

    void main() {
        posInterp = position;
        colorInterp = vertColor;
        vec4 pos_post_rotation = vec4(position, 0.0, 1.0) * rotationMatrix;
        gl_Position = modelMatrix * vec4(pos_post_rotation.xy * vec2(1.0, aspect_ratio), 0.0, 1.0);
    }
'''

# language=GLSL
vertex_shader_quad = '''
    in vec2 position;
    in vec2 uv;

    out vec2 uvInterp;

    void main() {
        uvInterp = uv;
        gl_Position = vec4(position, 0.0, 1.0);
    }
'''

# language=GLSL
fragment_shader_ghost = '''
    #define E 2.71828
    uniform vec4 color;
    uniform float empty;
    uniform float master_intensity;

    in vec2 posInterp;
    in vec4 colorInterp;

    out vec4 FragColor;

    void main() {
        float center = sqrt(pow(posInterp.x, 2.0) + pow(posInterp.y, 2.0));
        float gauss = 0.4 * pow(E, -(pow(center, 2.0) / 0.3));
        float edge = (1.0 - pow(colorInterp.x, 40.0)) - (gauss * empty);
        FragColor = color * edge * master_intensity;
    }
'''

# language=GLSL
fragment_shader_flare = '''
    #define E 2.71828
    #define PI 3.14159
    
    uniform vec4 color;
    uniform float size;
    uniform float intensity;
    uniform vec2 flare_position;
    uniform float aspect_ratio;
    uniform float blades;
    uniform float use_rays;
    uniform float rotation;
    uniform float master_intensity;

    in vec2 uvInterp;

    out vec4 FragColor;
    
    float gauss(float x, float center, float std_dev) {
        return pow(E, -(pow(x - center, 2.0) / std_dev));
    }
    
    float rays(float distance, float norm_angle) {
        float angle = fract(norm_angle * blades);
        float ray_centers = 1.0 - abs(angle * 2.0 - 1.0);
        ray_centers = pow(ray_centers, distance * 40.0) * max(1.0 - distance, 0.0);
        
        float rays_center = 2.0 * gauss(distance, 0.0, 0.02);
        
        return (ray_centers + rays_center) * use_rays;
    }

    void main() {
        vec2 flare_base = uvInterp - flare_position;
        float dist = sqrt( pow(flare_base.x * aspect_ratio, 2.0) + pow(flare_base.y, 2.0) ); // [0.0; 1.0]
        
        float flare = intensity * gauss(dist, 0.0, size / 100.0);
        
        // angle component of polar coordinates
        float angle = acos(flare_base.x * aspect_ratio / dist);
        if (flare_base.y < 0.0) {
            angle = -acos(flare_base.x * aspect_ratio / dist);
        }
        
        // normalize
        angle = ((angle + rotation) / (2.0 * PI));
        
        float rays_value = rays(dist, angle);
        
        float sum = flare + rays_value;
        
        FragColor = vec4(sum, sum, sum, 1.0) * color * intensity * master_intensity;
    }
'''