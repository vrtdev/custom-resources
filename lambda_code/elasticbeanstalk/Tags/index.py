from cfn_custom_resource import CloudFormationCustomResource


class Tags(CloudFormationCustomResource):
    def validate(self):
        self.environmentArn = self.resource_properties['EnvironmentArn']
        self.tags = self.resource_properties['Tags']

    @staticmethod
    def tags_to_update(tags):
        return list(map(lambda tag: {'Key': tag[0], 'Value': tag[1]}, tags.items()))

    def update_tags(self):
        client = self.get_boto3_session().client('elasticbeanstalk')
        client.update_tags_for_resource(
            ResourceArn=self.environmentArn,
            TagsToAdd=self.tags_to_update(self.tags)
        )
        return {'TagsToUpdate': self.tags_to_update(self.tags)}

    def create(self):
        return self.update_tags()

    def update(self):
        return self.update_tags()

    def delete(self):
        # Deleting not supported for now. Tags will disappear when environment is deleted.
        pass


handler = Tags.get_handler()
