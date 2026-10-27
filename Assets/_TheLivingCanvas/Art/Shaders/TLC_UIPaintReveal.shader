// Revelado pintado para UI (Image): _Reveal 0..1 descubre el sprite como pincelada, mancha de tinta o disolución.
// Barato: ruido procedural, sin texturas extra. Compatible con máscaras y Canvas de UGUI.
Shader "TLC/UI/PaintReveal"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _Reveal ("Reveal", Range(0,1)) = 1
        [KeywordEnum(Brush, Ink, Dissolve)] _Mode ("Mode", Float) = 0
        _Soft ("Edge softness", Range(0.01,0.5)) = 0.15
        _Seed ("Seed", Float) = 0

        _StencilComp ("Stencil Comparison", Float) = 8
        _Stencil ("Stencil ID", Float) = 0
        _StencilOp ("Stencil Operation", Float) = 0
        _StencilWriteMask ("Stencil Write Mask", Float) = 255
        _StencilReadMask ("Stencil Read Mask", Float) = 255
        _ColorMask ("Color Mask", Float) = 15
        [Toggle(UNITY_UI_ALPHACLIP)] _UseUIAlphaClip ("Use Alpha Clip", Float) = 0
    }

    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }
        Stencil
        {
            Ref [_Stencil]
            Comp [_StencilComp]
            Pass [_StencilOp]
            ReadMask [_StencilReadMask]
            WriteMask [_StencilWriteMask]
        }
        Cull Off
        Lighting Off
        ZWrite Off
        ZTest [unity_GUIZTestMode]
        Blend SrcAlpha OneMinusSrcAlpha
        ColorMask [_ColorMask]

        Pass
        {
            Name "Default"
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 2.0
            #pragma multi_compile_local _MODE_BRUSH _MODE_INK _MODE_DISSOLVE
            #pragma multi_compile_local _ UNITY_UI_CLIP_RECT
            #pragma multi_compile_local _ UNITY_UI_ALPHACLIP
            #include "UnityCG.cginc"
            #include "UnityUI.cginc"

            struct appdata { float4 vertex : POSITION; float4 color : COLOR; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct v2f { float4 vertex : SV_POSITION; fixed4 color : COLOR; float2 uv : TEXCOORD0; float4 worldPosition : TEXCOORD1; UNITY_VERTEX_OUTPUT_STEREO };

            sampler2D _MainTex;
            fixed4 _Color;
            fixed4 _TextureSampleAdd;
            float4 _ClipRect;
            float4 _MainTex_ST;
            float _Reveal, _Soft, _Seed;

            float hash21(float2 p) { p = frac(p * float2(123.34, 456.21)); p += dot(p, p + 45.32); return frac(p.x * p.y); }
            float vnoise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(hash21(i), hash21(i + float2(1, 0)), f.x),
                            lerp(hash21(i + float2(0, 1)), hash21(i + float2(1, 1)), f.x), f.y);
            }

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.worldPosition = v.vertex;
                o.vertex = UnityObjectToClipPos(o.worldPosition);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                o.color = v.color * _Color;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                half4 col = (tex2D(_MainTex, i.uv) + _TextureSampleAdd) * i.color;
                float2 uv = i.uv;
                float coord;
                #if defined(_MODE_BRUSH)
                    // Barrido horizontal con cerdas: el borde avanza irregular, con estrías por fila.
                    float streak = vnoise(float2(uv.y * 38.0 + _Seed, 3.1));
                    float wob = vnoise(float2(uv.x * 4.0 + _Seed, uv.y * 3.0));
                    coord = uv.x + (streak - 0.5) * 0.22 + (wob - 0.5) * 0.14;
                #elif defined(_MODE_INK)
                    // Mancha que crece desde el centro con borde orgánico.
                    float n = vnoise(uv * 5.0 + _Seed) * 0.7 + vnoise(uv * 13.0 + _Seed) * 0.3;
                    coord = length(uv - 0.5) * 1.3 + (n - 0.5) * 0.5;
                #else
                    coord = vnoise(uv * 24.0 + _Seed) * 0.6 + vnoise(uv * 7.0 + _Seed) * 0.4;
                #endif
                float r = lerp(-0.4, 1.4, _Reveal);
                col.a *= 1.0 - smoothstep(r - _Soft, r, coord);

                #ifdef UNITY_UI_CLIP_RECT
                col.a *= UnityGet2DClipping(i.worldPosition.xy, _ClipRect);
                #endif
                #ifdef UNITY_UI_ALPHACLIP
                clip(col.a - 0.001);
                #endif
                return col;
            }
            ENDCG
        }
    }
}
