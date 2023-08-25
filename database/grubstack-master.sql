--
-- PostgreSQL database dump
--

-- Dumped from database version 14.8 (Ubuntu 14.8-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.8 (Ubuntu 14.8-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: gs_log; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_log (
    log_id integer NOT NULL,
    log_created timestamp with time zone,
    log_asctime text,
    log_name text,
    log_loglevel integer,
    log_loglevelname text,
    log_message text,
    log_args text,
    log_module text,
    log_funcname text,
    log_lineno integer,
    log_exception text,
    log_process integer,
    log_thread text,
    log_threadname text
);


ALTER TABLE public.gs_log OWNER TO grubstack;

--
-- Name: gs_log_log_id_seq; Type: SEQUENCE; Schema: public; Owner: grubstack
--

CREATE SEQUENCE public.gs_log_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gs_log_log_id_seq OWNER TO grubstack;

--
-- Name: gs_log_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: grubstack
--

ALTER SEQUENCE public.gs_log_log_id_seq OWNED BY public.gs_log.log_id;


--
-- Name: gs_product; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_product (
    product_id integer NOT NULL,
    product_name text,
    product_description text,
    is_front_end_app boolean
);


ALTER TABLE public.gs_product OWNER TO grubstack;

--
-- Name: gs_products_product_id_seq; Type: SEQUENCE; Schema: public; Owner: grubstack
--

CREATE SEQUENCE public.gs_products_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gs_products_product_id_seq OWNER TO grubstack;

--
-- Name: gs_products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: grubstack
--

ALTER SEQUENCE public.gs_products_product_id_seq OWNED BY public.gs_product.product_id;


--
-- Name: gs_tenant_app; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_tenant_app (
    app_id integer NOT NULL,
    tenant_id text,
    product_id integer,
    app_url text
);


ALTER TABLE public.gs_tenant_app OWNER TO grubstack;

--
-- Name: gs_user_app_app_id_seq; Type: SEQUENCE; Schema: public; Owner: grubstack
--

CREATE SEQUENCE public.gs_user_app_app_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gs_user_app_app_id_seq OWNER TO grubstack;

--
-- Name: gs_user_app_app_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: grubstack
--

ALTER SEQUENCE public.gs_user_app_app_id_seq OWNED BY public.gs_tenant_app.app_id;


--
-- Name: gs_user_shared_app; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_user_shared_app (
    app_id integer,
    user_id text
);


ALTER TABLE public.gs_user_shared_app OWNER TO grubstack;

--
-- Name: gs_user_tenant; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_user_tenant (
    user_id text NOT NULL,
    tenant_id text NOT NULL,
    is_owner boolean
);


ALTER TABLE public.gs_user_tenant OWNER TO grubstack;

--
-- Name: gs_version; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_version (
    pid integer,
    version character varying(12)
);


ALTER TABLE public.gs_version OWNER TO grubstack;

--
-- Name: gs_log log_id; Type: DEFAULT; Schema: public; Owner: grubstack
--

ALTER TABLE ONLY public.gs_log ALTER COLUMN log_id SET DEFAULT nextval('public.gs_log_log_id_seq'::regclass);


--
-- Name: gs_product product_id; Type: DEFAULT; Schema: public; Owner: grubstack
--

ALTER TABLE ONLY public.gs_product ALTER COLUMN product_id SET DEFAULT nextval('public.gs_products_product_id_seq'::regclass);


--
-- Name: gs_tenant_app app_id; Type: DEFAULT; Schema: public; Owner: grubstack
--

ALTER TABLE ONLY public.gs_tenant_app ALTER COLUMN app_id SET DEFAULT nextval('public.gs_user_app_app_id_seq'::regclass);


--
-- Name: gs_log gs_log_pkey; Type: CONSTRAINT; Schema: public; Owner: grubstack
--

ALTER TABLE ONLY public.gs_log
    ADD CONSTRAINT gs_log_pkey PRIMARY KEY (log_id);


--
-- PostgreSQL database dump complete
--
