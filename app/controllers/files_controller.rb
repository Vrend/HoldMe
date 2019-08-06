class FilesController < ApplicationController
	def new
	end
	def create
			render plain: params[:file].inspect
	end
end
