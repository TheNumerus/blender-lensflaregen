uniform vec4 color;
uniform float size;
uniform float intensity;
uniform vec2 flare_position;
uniform float aspect_ratio;
uniform float blades;
uniform float use_rays;
uniform float rotation;
uniform float master_intensity;
uniform float anamorphic;
uniform vec2 res;
uniform sampler2D noise;

in vec2 uvInterp;

out vec4 FragColor;

float rays(float distance, float norm_angle) {
    float angle = norm_angle * 2.0 * PI * blades + PI;
    float distance_limit = max(1.0 - distance, 0.0);
    float ray_centers = pow(max(cos(angle), 0.0), 8.0) * distance_limit;

    return ray_centers;
}

float radial_noise(float dist, float angle) {
    float rot = 0.1;

    mat2 noise_rot;
    noise_rot[0] = vec2(-cos(rot), sin(rot));
    noise_rot[1] = vec2(-sin(rot), cos(rot));

    return texture(noise, vec2(dist * 0.001, angle) * noise_rot * 5.0).r;
}

void main() {
    vec2 flare_base = uvInterp - flare_position;
    float dist = sqrt( pow(flare_base.x * aspect_ratio, 2.0) + pow(flare_base.y, 2.0) ); // [0.0; 1.0]

    // angle component of polar coordinates
    float angle = acos(flare_base.x * aspect_ratio / dist);
    if (flare_base.y < 0.0) {
        angle = -acos(flare_base.x * aspect_ratio / dist);
    }

    // normalize
    angle += PI / 2.0;
    angle = ((angle + rotation) / (2.0 * PI));

    float rad_noise = radial_noise(dist, angle);

    float noise_ring_extrusion = mix(cos(angle * 2.0 * PI * blades + PI), 1.0, 0.95);

    float blade_count_to_ray_intensity = min(max((-blades + 18.0) / 12.0, 0.0), 1.0);

    float noise_ring_intensity = gauss(dist * noise_ring_extrusion, 0.21, 0.01);
    float noise_ring = rad_noise * noise_ring_intensity;

    float flare = gauss(dist, 0.0, size / 100.0);

    float rays_value = mix(noise_ring, rays(dist, angle) * rad_noise, blade_count_to_ray_intensity);

    float ray_center = 2.0 * gauss(dist, 0.0, 0.02);

    float sum = (flare * intensity) + ((rays_value + ray_center) * use_rays);

    if (anamorphic > 0.5) {
        float anam_ring = (noise_ring - 0.5) * 0.2;
        float anam_flare = (gauss(flare_base.x * aspect_ratio, 0.0, 0.01) * gauss(flare_base.y, 0.0, 0.01) + anam_ring) * intensity;

        float ray_distort = (1.0 - pow(anam_flare, 1.0) * 1.0);
        float ray_fade = pow(abs(min(pow(gauss(flare_base.x, 0.0, 1.0), 1.0), 1.0)), 0.5);

        float anam_ray = max(1.0 - pow(max(abs(flare_base.y * 3.0) * ray_distort / ray_fade, 0.0), 0.5) * 2.0, 0.0) * use_rays;

        float anam = max(anam_flare + anam_ray * 1.0, anam_ray) * gauss(flare_base.x, 0.0, 0.5);

        FragColor = vec4(anam, anam, anam, 1.0) * color * master_intensity + texture(noise, uvInterp * res).r / 255.0;
    } else {
        FragColor = vec4(sum, sum, sum, 1.0) * color * master_intensity + texture(noise, uvInterp * res).r / 255.0;
    }
}