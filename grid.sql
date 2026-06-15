create table public.password_resets (
  email text not null,
  token text not null,
  created_at text not null,
  constraint pk_password_resets primary key (email)
) TABLESPACE pg_default;



create table public.rovers (
  id bigint generated always as identity not null,
  nome text not null,
  codigo text not null,
  ativo boolean not null,
  criado_em timestamp with time zone not null,
  mac_address text not null,
  email_dono text not null,
  constraint pk_rovers primary key (id),
  constraint uq_rovers_codigo unique (codigo),
  constraint uq_rovers_nome unique (nome)
) TABLESPACE pg_default;



create table public.rovers (
  id bigint generated always as identity not null,
  nome text not null,
  codigo text not null,
  ativo boolean not null,
  criado_em timestamp with time zone not null,
  mac_address text not null,
  email_dono text not null,
  constraint pk_rovers primary key (id),
  constraint uq_rovers_codigo unique (codigo),
  constraint uq_rovers_nome unique (nome)
) TABLESPACE pg_default;




create table public.users (
  id bigint generated always as identity not null,
  username text not null,
  email text not null,
  password character varying not null,
  aprovado boolean null,
  created_at timestamp with time zone not null,
  role text null,
  bloqueado boolean null,
  rover_id bigint null,
  telemovel text not null,
  constraint pk_users primary key (id),
  constraint uq_users_email unique (email),
  constraint uq_users_username unique (username),
  constraint fk_users_rovers foreign KEY (rover_id) references rovers (id) on delete set null
) TABLESPACE pg_default;