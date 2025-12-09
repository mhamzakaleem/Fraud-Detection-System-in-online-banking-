create database fraud;
use fraud;

create table users (
    user_id int primary key identity(1,1),
    name varchar(100) not null,
    email varchar(100) not null unique,
    phone_number varchar(20) not null unique,
    password varchar(255),
    balance decimal(18,2) default 0.00,
    account_status varchar(20) default 'Active',
    created_at datetime default getdate()
);

create table transactions (
    transaction_id int primary key identity(1,1),
    sender_id int not null,
    receiver_id int not null,
    amount decimal(18,2) not null,
    currency varchar(10),
    location varchar(100),
    device_info varchar(255),
    ip_address varchar(50),
    timestamp datetime default getdate(),
    status varchar(20) default 'Completed',
    foreign key (sender_id) references users(user_id),
    foreign key (receiver_id) references users(user_id)
);

create table fraud_alerts (
    alert_id int primary key identity(1,1),
    transaction_id int,
    user_id int,
    fraud_score int,
    reason varchar(255),
    created_at datetime default getdate(),
    foreign key (transaction_id) references transactions(transaction_id),
    foreign key (user_id) references users(user_id)
);

create table device_usage (
    device_id int primary key identity(1,1),
    user_id int,
    device_type varchar(100),
    os_name varchar(100),
    ip_address varchar(50),
    location varchar(100),
    last_used_at datetime,
    foreign key (user_id) references users(user_id)
);

create table logs (
    log_id int primary key identity(1,1),
    user_id int,
    action varchar(255),
    timestamp datetime default getdate(),
    foreign key (user_id) references users(user_id)
);

insert into users (name, email, phone_number, password, balance, account_status)
values
('Admin', 'admin@email.com', '0000', 'admin123', 9999999.00, 'Active'),
('Hamza', 'hamza@emal.com', '03000000001', 'hamza123', 1000.00, 'Active'),
('Ali', 'ali@email.com', '03000000002', 'ali123', 1000.00, 'Active'),
('Umar', 'umar@email.com', '03000000003', 'umar123', 1000.00, 'Active'),
('Usman', 'usman@email.com', '03000000004', 'usman123', 1000.00, 'Active'),
('Bilal', 'bilal@email.com', '03000000005', 'bilal123', 1000.00, 'Active'),
('Hassan', 'hassan@email.com', '03000000006', 'hassan123', 1000.00, 'Active'),
('Hussain', 'hussain@email.com', '03000000007', 'hussain123', 1000.00, 'Active'),
('Zain', 'zain@email.com', '03000000008', 'zain123', 1000.00, 'Active'),
('Saad', 'saad@email.com', '03000000010', 'saad123', 1000.00, 'Active'),
('Kashif', 'kashif@email.com', '03000000011', 'kashif123', 1000.00, 'Active'),
('Arif', 'arif@email.com', '03000000012', 'arif123', 1000.00, 'Active'),
('Farhan', 'farhan@email.com', '03000000013', 'farhan123', 1000.00, 'Active'),
('Noman', 'noman@email.com', '03000000014', 'noman123', 1000.00, 'Active'),
('Sami', 'sami@email.com', '03000000015', 'sami123', 1000.00, 'Active'),
('Yasir', 'yasir@email.com', '03000000016', 'yasir123', 1000.00, 'Active'),
('Zeeshan', 'zeeshan@email.com', '03000000017', 'zeeshan123', 1000.00, 'Active'),
('Tariq', 'tariq@email.com', '03000000018', 'tariq123', 1000.00, 'Active'),
('Nadeem', 'nadeem@email.com', '03000000019', 'nadeem123', 1000.00, 'Active'),
('Amir', 'amir@email.com', '03000000020', 'amir123', 1000.00, 'Active');

create index indexuemail on users(email);
create index indexuphone on users(phone_number);
create index indextsender on transactions(sender_id);
create index indextreceiver on transactions(receiver_id);
create index indexttime on transactions(timestamp);
create index indexfuser on fraud_alerts(user_id);

select * from users;
select * from logs;
select * from device_usage;
select * from transactions;
select * from fraud_alerts

update users
set email = 'hamza@email.com'
where user_id = 2;

-- Group Members
-- Muhammad Hamza Kaleem (FA23-BESE-0003)
-- Muhammad Safwan (FA23-BESE-0030)
-- Muhammad Hasnain (FA23-BESE-0040)
-- Usman Maloob (FA23-BESE-0049)
select u.name, f.reason, f.created_at 
from fraud_alerts f 
join users u on f.user_id = u.user_id 
order by f.created_at desc;

select u.user_id, u.name, f.reason, f.created_at 
from fraud_alerts f 
join users u on f.user_id = u.user_id 
order by f.created_at desc;

select u.user_id, u.name, l.action, l.timestamp 
from logs l 
join users u on l.user_id = u.user_id 
order by l.timestamp desc;
