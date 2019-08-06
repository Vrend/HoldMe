class PagesController < ApplicationController
	def about
		@title = 'About This App'
		@content = 'This is the about page'
	end
end
