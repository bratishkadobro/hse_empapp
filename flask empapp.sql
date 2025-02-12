PGDMP     $            	        }            flask_emp_app    15.2    15.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            	           1262    147662    flask_emp_app    DATABASE     �   CREATE DATABASE flask_emp_app WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Russian_Russia.1251';
    DROP DATABASE flask_emp_app;
                postgres    false            �            1259    147663    departments    TABLE     W   CREATE TABLE public.departments (
    id integer NOT NULL,
    department_name text
);
    DROP TABLE public.departments;
       public         heap    postgres    false            �            1259    147668    departments_id_seq    SEQUENCE     �   ALTER TABLE public.departments ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.departments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    214            �            1259    147675    persons    TABLE     �   CREATE TABLE public.persons (
    id integer NOT NULL,
    full_name text,
    date date,
    department_id real,
    job_title_id real,
    reason text,
    added_by text
);
    DROP TABLE public.persons;
       public         heap    postgres    false            �            1259    147682    persons_id_seq    SEQUENCE     �   ALTER TABLE public.persons ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.persons_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    216            �            1259    147689    users    TABLE       CREATE TABLE public.users (
    id bigint NOT NULL,
    username text,
    password text,
    active boolean DEFAULT true,
    department_owner_id real,
    realname text,
    email text,
    force_pwd boolean DEFAULT true NOT NULL,
    is_admin boolean DEFAULT false NOT NULL
);
    DROP TABLE public.users;
       public         heap    postgres    false            �            1259    147695    users_id_seq    SEQUENCE     �   ALTER TABLE public.users ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);
            public          postgres    false    218            s           2606    147699    persons persons_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.persons DROP CONSTRAINT persons_pkey;
       public            postgres    false    216            u           2606    147703    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public            postgres    false    218           