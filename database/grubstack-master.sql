--
-- Name: gs_tenant; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_tenant (
    tenant_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    status VARCHAR(64) CHECK (status IN ('active', 'suspended'))
);

ALTER TABLE public.gs_tenant OWNER TO grubstack;

--
-- Name: gs_user; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_user (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    user_id SERIAL NOT NULL PRIMARY KEY,
    username text NOT NULL,
    password text,
    create_time timestamp with time zone NOT NULL,
    access_time timestamp with time zone,
    last_ip character varying(15),
    reset_token text,
    is_active boolean DEFAULT false,
    first_name character varying(120),
    last_name character varying(120),
    is_subscribed boolean
);

ALTER TABLE public.gs_user OWNER TO grubstack;

--
-- Name: gs_jwt; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_jwt (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    jwt_id SERIAL PRIMARY KEY NOT NULL,
    jwt_token text,
    jwt_token_type text,
    jwt_jti text,
    jwt_user_identity text,
    jwt_expires timestamp with time zone,
    jwt_username text,
    jwt_revoked boolean DEFAULT false,
    jwt_created timestamp with time zone DEFAULT now()
);

ALTER TABLE public.gs_jwt OWNER TO grubstack;

--
-- Name: gs_log; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_log (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    log_id SERIAL PRIMARY KEY NOT NULL,
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
-- Name: gs_permission; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_permission (
    permission_id SERIAL PRIMARY KEY NOT NULL,
    name character varying(255),
    description text
);

ALTER TABLE public.gs_permission OWNER TO grubstack;

--
-- Name: gs_user_permission; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_user_permission (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);

ALTER TABLE public.gs_user_permission OWNER TO grubstack;

--
-- Name: gs_role; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_role (
    role_id SERIAL PRIMARY KEY NOT NULL,
    name text,
    descripion text
);

ALTER TABLE public.gs_role OWNER TO grubstack;

--
-- Name: gs_user_role; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_user_role (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,
    user_id integer NOT NULL,
    role_id integer NOT NULL
);

ALTER TABLE public.gs_user_role OWNER TO grubstack;

--                                                                                                                             
-- Name: gs_store; Type: TABLE; Schema: public; Owner: grubstack                                                               
--                                                                                                                             
                                                                                                                               
CREATE TABLE public.gs_store ( 
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    store_id SERIAL PRIMARY KEY NOT NULL,                                                                                                 
    name text,                                                                                                                 
    address1 text,                                                                                                             
    city character varying(60),                                                                                                
    state character varying(50),                                                                                               
    postal character varying(50),                                                                                              
    store_type text,                                                                                                           
    thumbnail_url text                                                                                                         
);                                                                                                                             

ALTER TABLE public.gs_store OWNER TO grubstack;                                                                                

--
-- Name: gs_ingredient; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    ingredient_id SERIAL PRIMARY KEY NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    thumbnail_url text,
    calories double precision,
    fat double precision,
    saturated_fat double precision,
    trans_fat double precision,
    cholesterol double precision,
    sodium double precision,
    carbs double precision,
    protein double precision,
    sugar double precision,
    fiber double precision,
    price double precision
);

ALTER TABLE public.gs_ingredient OWNER TO grubstack;

--
-- Name: gs_menu; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_menu (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    menu_id SERIAL PRIMARY KEY NOT NULL,
    name text,
    description text,
    thumbnail_url text
);

ALTER TABLE public.gs_menu OWNER TO grubstack;

--
-- Name: gs_menu_item; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_menu_item (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    menu_id integer NOT NULL,
    item_id integer NOT NULL,
    price double precision,
    sale_price double precision,
    is_onsale boolean
);

ALTER TABLE public.gs_menu_item OWNER TO grubstack;

--
-- Name: gs_item; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_item (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    item_id SERIAL PRIMARY KEY NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    thumbnail_url text NOT NULL
);

ALTER TABLE public.gs_item OWNER TO grubstack;

--
-- Name: gs_item_ingredient; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_item_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    item_id integer NOT NULL,
    ingredient_id integer NOT NULL,
    is_optional boolean,
    is_addon boolean,
    is_extra boolean
);


ALTER TABLE public.gs_item_ingredient OWNER TO grubstack;

--
-- Name: gs_variety; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_variety (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    variety_id SERIAL PRIMARY KEY NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    thumbnail_url text NOT NULL
);

ALTER TABLE public.gs_variety OWNER TO grubstack;

--
-- Name: gs_variety_ingredient; Type: TABLE; Schema: public; Owner: grubstack
--

CREATE TABLE public.gs_variety_ingredient (
    tenant_id UUID NOT NULL REFERENCES gs_tenant (tenant_id) ON DELETE RESTRICT,                                                                                                
    variety_id integer NOT NULL,
    ingredient_id integer NOT NULL
);


ALTER TABLE public.gs_variety_ingredient OWNER TO grubstack;


ALTER TABLE gs_tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_user_role ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_user_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_menu ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_menu_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_item_ingredient ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_variety ENABLE ROW LEVEL SECURITY;
ALTER TABLE gs_variety_ingredient ENABLE ROW LEVEL SECURITY;

ALTER TABLE gs_tenant FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_user FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_user_role FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_user_permission FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_store FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_ingredient FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_menu FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_menu_item FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_item FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_item_ingredient FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_variety FORCE ROW LEVEL SECURITY;
ALTER TABLE gs_variety_ingredient FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON gs_tenant USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_user USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_user_role USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_user_permission USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_store USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_menu USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_menu_item USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_item USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_item_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_variety USING (tenant_id = current_setting('app.tenant_id')::UUID);
CREATE POLICY tenant_isolation_policy ON gs_variety_ingredient USING (tenant_id = current_setting('app.tenant_id')::UUID);

INSERT INTO gs_permission VALUES (DEFAULT, 'ViewStores', 'Allow user to view stores');
INSERT INTO gs_permission VALUES (DEFAULT, 'MaintainStores', 'Allow user to to add, delete, and update stores');
INSERT INTO gs_permission VALUES (DEFAULT, 'ViewMenus', 'Allow user to view menus');
INSERT INTO gs_permission VALUES (DEFAULT, 'MaintainMenus', 'Allow user to to add, delete, and update menus');
INSERT INTO gs_permission VALUES (DEFAULT, 'ViewItems', 'Allow user to view items');
INSERT INTO gs_permission VALUES (DEFAULT, 'MaintainItems', 'Allow user to to add, delete, and update items');
INSERT INTO gs_permission VALUES (DEFAULT, 'ViewIngredients', 'Allow user to view ingredients');
INSERT INTO gs_permission VALUES (DEFAULT, 'MaintainIngredients', 'Allow user to to add, delete, and update ingredients');
INSERT INTO gs_permission VALUES (DEFAULT, 'ViewVarieties', 'Allow user to view varieties');
INSERT INTO gs_permission VALUES (DEFAULT, 'MaintainVarieties', 'Allow user to to add, delete, and update varieties');

INSERT INTO gs_role VALUES (DEFAULT, 'Administrator', 'Provides administrator access to the dashboard');
INSERT INTO gs_role VALUES (DEFAULT, 'Customer', 'Basic user account used for store access and purchases');
