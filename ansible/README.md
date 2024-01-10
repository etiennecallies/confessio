Deployment in production instructions.

## OVH

Create a public cloud instance `discovery` `d2-2` in Gravelines, on public network, using ubuntu 23.04, with a name like `confessio-1`. 

Add the following firewall configuration:
![OVHcloud.png](./OVHcloud.png)

Buy a domain and link DNS to your instance IP.
![Domaines.png](./Domaines-SSL-IONOS.png)

## AWS S3

We use S3 to backup postgresql daily and weekly.

Create two S3 buckets and an IAM user ([tutorial](https://kinsta.com/knowledgebase/amazon-s3-backups/)).
For security reasons, we don't want the IAM user to be able to delete backups.

Here is a policy (a little bit too permissive on resources though):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObjectAcl",
                "s3:GetObject",
                "s3:ListAllMyBuckets",
                "s3:ListBucket",
                "s3:GetBucketAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": "*"
        }
    ]
}
```

## Run ansible playbook

```shell
./deploy_prod.sh
```
This is mainly inspired by https://realpython.com/automating-django-deployments-with-fabric-and-ansible/