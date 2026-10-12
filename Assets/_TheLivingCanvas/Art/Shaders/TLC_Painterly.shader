// TLC/Painterly — material base de The Living Canvas (URP 17 / Unity 6, Forward+ compatible).
//
// FILOSOFIA (ver ART_DIRECTION.md): el shader COMPLEMENTA tu textura pintada, no la sustituye.
//   1. La textura (_BaseMap) manda: su color llega a pantalla casi intacto.
//   2. Una segunda textura de pincelada (_BrushMap) rompe la luz: el borde de la sombra sigue los trazos
//      en vez de ser una curva lisa, y el valor/tono varia un poco. Es opcional (Strength = 0 la apaga).
//   3. La luz es una rampa suave (sin brillo especular realista): da volumen sin borrar tus pinceladas.
//   4. La Descoloracion se controla con el global _TLC_Descolor (0..1) y, por material, con _DescolorResponse.
//      No es gris puro: deja algo de croma, enfria y cambia el contraste. Un color "protegido"
//      (_PreserveColor) puede resistirse a la Descoloracion (ej. el amarillo de la flor).
//
// LIMITACIONES: depende de las UVs del modelo (la textura pintada va por UV). _BrushSpace = World usa
// proyeccion por mundo para la pincelada (util en suelos y paredes sin UVs buenas). Sin lightmaps ni
// reflejos; sin transparencia.
Shader "TLC/Painterly"
{
    Properties
    {
        [Header(Painted texture)]
        [MainTexture] _BaseMap ("Painted texture", 2D) = "white" {}
        [MainColor] _BaseColor ("Tint", Color) = (1,1,1,1)

        [Header(Brush strokes)]
        _BrushMap ("Brush map (grey, 0.5 = neutral)", 2D) = "gray" {}
        _BrushStrength ("Brush value variation", Range(0, 1)) = 0.25
        _BrushBreakup ("Brush breaks shadow edge", Range(0, 1)) = 0.35
        _BrushScale ("Brush tiling (per UV or per metre)", Float) = 1
        _BrushRotation ("Brush rotation (deg)", Range(0, 360)) = 0
        [Enum(MeshUV, 0, World, 1)] _BrushSpace ("Brush space", Float) = 0

        [Header(Light)]
        _ShadowColor ("Shadow tint", Color) = (0.55, 0.60, 0.75, 1)
        _ShadowStrength ("Shadow tint strength", Range(0, 1)) = 0.6
        _LightThreshold ("Light/shadow threshold", Range(0, 1)) = 0.5
        _RampSoftness ("Ramp softness", Range(0.01, 0.5)) = 0.18
        _AmbientStrength ("Ambient strength", Range(0, 2)) = 1

        [Header(Descoloration)]
        _DescolorResponse ("Descolor response (0 = immune)", Range(0, 1)) = 1
        _ColdShift ("Cold shift", Range(0, 1)) = 0.5
        _DescolorContrast ("Contrast change", Range(-0.5, 0.5)) = 0.1
        _PreserveColor ("Preserved colour", Color) = (0.83, 0.65, 0.17, 1)
        _PreserveRange ("Preserved hue range", Range(0, 1)) = 0.25
        _PreserveAmount ("Preserve amount (0 = off)", Range(0, 1)) = 0

        [Header(Surface)]
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" "UniversalMaterialType" = "SimpleLit" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

        TEXTURE2D(_BaseMap);  SAMPLER(sampler_BaseMap);
        TEXTURE2D(_BrushMap); SAMPLER(sampler_BrushMap);

        // Global fijado por PainterlyDescolor (0 = color normal, 1 = Descoloracion completa).
        float _TLC_Descolor;

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _BrushStrength;
            half _BrushBreakup;
            float _BrushScale;
            half _BrushRotation;
            half _BrushSpace;
            half4 _ShadowColor;
            half _ShadowStrength;
            half _LightThreshold;
            half _RampSoftness;
            half _AmbientStrength;
            half _DescolorResponse;
            half _ColdShift;
            half _DescolorContrast;
            half4 _PreserveColor;
            half _PreserveRange;
            half _PreserveAmount;
            half _Cull;
        CBUFFER_END
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex Vert
            #pragma fragment Frag

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fog

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                float3 normalWS : TEXCOORD2;
                half fogFactor : TEXCOORD3;
            };

            Varyings Vert(Attributes input)
            {
                Varyings o;
                VertexPositionInputs vp = GetVertexPositionInputs(input.positionOS.xyz);
                o.positionCS = vp.positionCS;
                o.positionWS = vp.positionWS;
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.uv = TRANSFORM_TEX(input.uv, _BaseMap);
                o.fogFactor = ComputeFogFactor(vp.positionCS.z);
                return o;
            }

            // Proyeccion por mundo: elige el plano segun la normal dominante.
            float2 WorldPlanarUV(float3 posWS, float3 nWS)
            {
                float3 n = abs(nWS);
                if (n.y >= n.x && n.y >= n.z) return posWS.xz;
                if (n.x >= n.z) return posWS.zy;
                return posWS.xy;
            }

            half Luma(half3 c) { return dot(c, half3(0.2126h, 0.7152h, 0.0722h)); }

            // Descoloracion: no es escala de grises. Conserva algo de croma, enfria y ajusta contraste.
            half3 ApplyDescolor(half3 c, half d)
            {
                half l = Luma(c);
                half3 g = lerp(c, l.xxx, d * 0.8h);
                g = lerp(g, g * half3(0.90h, 0.96h, 1.07h), d * _ColdShift);
                g = max(0, (g - 0.18h) * (1 + _DescolorContrast * d) + 0.18h);
                return g;
            }

            // 0..1: cuanto se parece este color al color protegido (por direccion de croma).
            half PreserveWeight(half3 c)
            {
                half l = Luma(c);
                half3 cc = c - l;
                half3 pc = _PreserveColor.rgb - Luma(_PreserveColor.rgb);
                half chroma = max(c.r, max(c.g, c.b)) - min(c.r, min(c.g, c.b));
                half sim = saturate(dot(normalize(cc + 1e-4h), normalize(pc + 1e-4h)));
                return smoothstep(1 - _PreserveRange, 1, sim) * saturate(chroma * 6) * _PreserveAmount;
            }

            half Ramp(half w)
            {
                return smoothstep(_LightThreshold - _RampSoftness, _LightThreshold + _RampSoftness, w);
            }

            half4 Frag(Varyings input, FRONT_FACE_TYPE facing : FRONT_FACE_SEMANTIC) : SV_Target
            {
                float3 nWS = normalize(input.normalWS);
                nWS = IS_FRONT_VFACE(facing, nWS, -nWS); // geometria de doble cara (hojas, petalos)

                half3 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv).rgb * _BaseColor.rgb;

                // Pincelada: UV de malla o proyeccion de mundo, con escala y rotacion.
                float2 buv = (_BrushSpace > 0.5h) ? WorldPlanarUV(input.positionWS, nWS) : input.uv;
                float s, c;
                sincos(radians(_BrushRotation), s, c);
                buv = float2(c * buv.x - s * buv.y, s * buv.x + c * buv.y) * _BrushScale;
                half brush = SAMPLE_TEXTURE2D(_BrushMap, sampler_BrushMap, buv).r - 0.5h; // -0.5..0.5

                albedo *= 1 + brush * 2 * _BrushStrength;

                // Descoloracion (solo sobre el color, no sobre la luz).
                half d = saturate(_TLC_Descolor) * _DescolorResponse;
                d *= 1 - PreserveWeight(albedo);
                albedo = ApplyDescolor(albedo, d);

                // Luz: rampa suave; la pincelada desplaza el umbral para que el borde de la sombra siga los trazos.
                half3 shadowTint = lerp(1, _ShadowColor.rgb, _ShadowStrength);
                half3 ambient = SampleSH(nWS) * _AmbientStrength;

                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord, input.positionWS, half4(1, 1, 1, 1));
                half w = dot(nWS, mainLight.direction) * 0.5h + 0.5h + brush * _BrushBreakup;
                half ramp = Ramp(w) * mainLight.shadowAttenuation * mainLight.distanceAttenuation;

                half3 direct = mainLight.color * ramp;
                half3 lit = ambient * lerp(shadowTint, 1, ramp) + direct;

                #if defined(_ADDITIONAL_LIGHTS)
                    InputData inputData = (InputData)0;
                    inputData.positionWS = input.positionWS;
                    inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(input.positionCS);
                    uint pixelLightCount = GetAdditionalLightsCount();

                    #if USE_CLUSTER_LIGHT_LOOP
                    [loop] for (uint dirIndex = 0; dirIndex < min(URP_FP_DIRECTIONAL_LIGHTS_COUNT, MAX_VISIBLE_LIGHTS); dirIndex++)
                    {
                        Light dl = GetAdditionalLight(dirIndex, input.positionWS, half4(1, 1, 1, 1));
                        half dw = dot(nWS, dl.direction) * 0.5h + 0.5h + brush * _BrushBreakup;
                        lit += dl.color * Ramp(dw) * dl.distanceAttenuation * dl.shadowAttenuation;
                    }
                    #endif

                    LIGHT_LOOP_BEGIN(pixelLightCount)
                        Light al = GetAdditionalLight(lightIndex, input.positionWS, half4(1, 1, 1, 1));
                        half aw = dot(nWS, al.direction) * 0.5h + 0.5h + brush * _BrushBreakup;
                        lit += al.color * Ramp(aw) * al.distanceAttenuation * al.shadowAttenuation;
                    LIGHT_LOOP_END
                #endif

                half3 color = albedo * lit;
                color = MixFog(color, input.fogFactor);
                return half4(color, 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex ShadowVert
            #pragma fragment ShadowFrag
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings ShadowVert(Attributes input)
            {
                Varyings o;
                float3 positionWS = TransformObjectToWorld(input.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(input.normalOS);
                #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                    float3 lightDirectionWS = normalize(_LightPosition - positionWS);
                #else
                    float3 lightDirectionWS = _LightDirection;
                #endif
                o.positionCS = ApplyShadowClamping(TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDirectionWS)));
                return o;
            }

            half4 ShadowFrag(Varyings input) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex DepthVert
            #pragma fragment DepthFrag

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings DepthVert(Attributes input)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                return o;
            }

            half DepthFrag(Varyings input) : SV_Target { return input.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On
            Cull [_Cull]

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex NormVert
            #pragma fragment NormFrag
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; };

            Varyings NormVert(Attributes input)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                return o;
            }

            half4 NormFrag(Varyings input) : SV_Target
            {
                #if defined(_GBUFFER_NORMALS_OCT)
                    float3 n = normalize(input.normalWS);
                    float2 oct = PackNormalOctQuadEncode(n);
                    float2 remapped = saturate(oct * 0.5 + 0.5);
                    return half4(PackFloat2To888(remapped), 0);
                #else
                    return half4(NormalizeNormalPerPixel(input.normalWS), 0);
                #endif
            }
            ENDHLSL
        }
    }
    FallBack Off
}
