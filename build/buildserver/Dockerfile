FROM phusion/passenger-ruby22:latest

ENV HOME=/root \
RAILS_VERSION='~> 3.2'
CMD ["/sbin/my_init"]

RUN apt-get update -qq && \
apt-get upgrade -y -o Dpkg::Options::="--force-confold" && \
gem install rails --version "$RAILS_VERSION" && \
apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /pd_build

